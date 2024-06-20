import asyncio
import copy
import json
import time
from datetime import datetime
from typing import Optional

import aiohttp
import requests
from loguru import logger

import apm2

EPOCH_START = datetime(1970, 1, 1)


def m2r_datetime_to_epoch(datetime_str: str) -> float:
    """
    Turn a mavlink2rest date string (with nanoseconds) into seconds-since-epoch, comparable to time.time()
    """
    dt = datetime.strptime(datetime_str[0:-4] + 'Z', '%Y-%m-%dT%H:%M:%S.%fZ')
    return(dt - EPOCH_START).total_seconds()


def chars_to_str(param_id_chars: list[str]) -> str:
    """
    ['E', 'K', '3', '_', 'S', 'R', 'C', '1', '_', 'P', 'O', 'S', 'X', 'Y', '\x00', '\x00'] -> 'EK3_SRC1_POSXY'
    """
    no_nulls = [x if x != '\x00' else '' for x in param_id_chars]
    return ''.join(no_nulls)


def str_to_chars(param_id: str, pad_len) -> list[str]:
    """
    'EK3_SRC1_POSXY' -> ['E', 'K', '3', '_', 'S', 'R', 'C', '1', '_', 'P', 'O', 'S', 'X', 'Y', '\x00', '\x00']
    """
    result = [c for c in param_id]
    if len(result) < pad_len:
        for i in range(pad_len - len(result)):
            result.append('\x00')
    return result


class MavClient:
    """
    Provide a wrapper around the mavlink2rest API.

    The primary connection to mavlink2rest is through a websocket. We listen to all messages and store the latest
    MAVLink message for each sys_id, comp_id, msg_id tuple. We also store all parameter values.

    The system is healthy if there is an open websocket delivering regular HEARTBEAT messages. If the system becomes
    unhealthy we delete the stored messages and parameters and start over.
    """

    def __init__(self, mavlink2rest_url: str, target_system=1, target_component=1):
        self._mavlink2rest_url = mavlink2rest_url
        self._target_system = target_system
        self._target_component = target_component

        # Track system health
        self._websocket_is_open = False
        self._receiving_heartbeats = False
        self._last_heartbeat_time = None

        # A list of message ids and frequencies that we need
        self._msg_frequencies: dict[int, float] = {}

        # MAVLink message callback
        self._msg_callback = None

        # Store all parameter values
        self._parameters: dict[str, float] = {}

        # Throttle param request messages
        self._param_request_burst_start = time.time()
        self._param_request_burst_count = 0

        # Store the most recent NAMED_VALUE_FLOAT message, by name, for the target system
        self._named_floats: dict[str, float] = {}

        # Cache MAVLink message templates
        self._template_cache: dict[str, any] = {}

    def _reset(self):
        logger.warning('ArduSub is down, clearing caches')
        self._parameters = {}
        self._named_floats = {}
        self._template_cache = {}
        self._receiving_heartbeats = False
        self._last_heartbeat_time = None

    def get_json(self, path: str) -> Optional[dict[str, any]]:
        """
        Get something from mavlink2rest
        """
        get_url = self._mavlink2rest_url + path
        try:
            response = requests.get(get_url)
            if response.status_code == 200:
                if response.text == 'None':
                    # Expected, e.g., requesting a message from a comp_id that does not exist
                    return None
                else:
                    return json.loads(response.text)
            else:
                logger.error(f'GET [{get_url}] status code {response.status_code}')
                return None
        except Exception as ex:
            logger.error(f'GET [{get_url}] exception: {ex}')
            return None

    def get_msg(self, msg_name: str, sys_id: int, comp_id: int, timeout: Optional[float]):
        """
        Get the most recent message for this (sys_id, comp_id, msg_name)
        If timeout is not None, then check the 'last_update' time and reject old messages
        """
        msg = self.get_json(f'/mavlink/vehicles/{sys_id}/components/{comp_id}/messages/{msg_name}')

        if msg is None:
            return None

        if timeout is not None:
            last_update = m2r_datetime_to_epoch(msg['status']['time']['last_update'])
            if time.time() - last_update > timeout:
                return None

        return msg

    def send_msg(self, info: str, msg: dict[str, any]) -> bool:
        """
        Post a MAVLink message to mavlink2rest
        """
        try:
            response = requests.post(self._mavlink2rest_url + '/mavlink', json=msg)
            if response.status_code == 200:
                return True
            else:
                logger.error(f'POST [{info}] status code {response.status_code}')
                return False
        except Exception as ex:
            logger.error(f'POST [{info}] exception: {ex}')
            return False

    def get_template(self, msg_name: str) -> Optional[dict[str, any]]:
        """
        Ask mavlink2rest for a MAVLink message template, and cache the result
        """
        if msg_name not in self._template_cache:
            template = self.get_json(f'/helper/mavlink?name={msg_name}')
            if template is None:
                # Perhaps mavlink2rest hasn't started yet, caller can try again later
                return None
            logger.info(f'new template {template}')
            self._template_cache[msg_name] = template

        # Return a copy of the template so the caller can modify it
        return copy.deepcopy(self._template_cache[msg_name])

    def _request_msg_frequencies(self):
        """
        Send MAV_CMD_SET_MESSAGE_INTERVAL messages
        Does not work for NAMED_VALUE_FLOAT, workarounds: set SR0_EXT_STAT or call _request_data_stream()
        """
        msg = self.get_template('COMMAND_LONG')
        if msg is not None:
            msg['message']['target_system'] = self._target_system
            msg['message']['target_component'] = self._target_component
            msg['message']['command'] = {'type': 'MAV_CMD_SET_MESSAGE_INTERVAL'}
            for msg_id, frequency in self._msg_frequencies.items():
                logger.info(f'request msg_id {msg_id} at {frequency} Hz')
                msg['message']['param1'] = msg_id
                msg['message']['param2'] = int(1000000 / frequency) if frequency > 0 else -1
                self.send_msg(f'COMMAND_LONG:MAV_CMD_SET_MESSAGE_INTERVAL:{msg_id}', msg)

    def _request_data_stream(self, stream_id: int, frequency=4):
        """
        Deprecated, but handy for getting NAMED_VALUE_FLOAT messages from ArduSub
        """
        msg = self.get_template('REQUEST_DATA_STREAM')
        if msg is not None:
            msg['message']['target_system'] = self._target_system
            msg['message']['target_component'] = self._target_component
            msg['message']['req_stream_id'] = stream_id
            msg['message']['req_message_rate'] = frequency
            msg['message']['start_stop'] = 1  # Start sending
            self.send_msg(f'REQUEST_DATA_STREAM:{stream_id}', msg)

    def _request_param(self, param_id: str):
        """
        Send a PARAM_REQUEST_READ message to the target system
        """
        msg = self.get_template('PARAM_REQUEST_READ')
        if msg is None:
            return

        # There appears to be a limit of 25 active requests somewhere, throttle requests to avoid hitting it
        now = time.time()
        if now - self._param_request_burst_start > 0.3:
            # Reset burst count
            self._param_request_burst_start = now
            self._param_request_burst_count = 0

        if self._param_request_burst_count >= 10:
            # Throttled
            return

        logger.warning(f'failed to get param {param_id}, send PARAM_REQUEST_READ message')
        msg['message']['target_system'] = self._target_system
        msg['message']['target_component'] = self._target_component
        msg['message']['param_index'] = -1
        msg['message']['param_id'] = str_to_chars(param_id, 16)
        self.send_msg(f'PARAM_REQUEST_READ:{param_id}', msg)
        self._param_request_burst_count += 1

    def _add_ws_text_msg(self, ws_msg: aiohttp.WSMessage):
        """
        Handle a websocket TEXT message
        """
        try:
            mav_msg = json.loads(ws_msg.data.strip())
        except Exception as ex:
            logger.error(f'_add_ws_msg exception: {ex}')
            return

        sys_id = mav_msg['header']['system_id']
        comp_id = mav_msg['header']['component_id']
        msg_name = mav_msg['message']['type']

        if sys_id == self._target_system and comp_id == self._target_component:
            if msg_name == 'HEARTBEAT':
                self._last_heartbeat_time = time.time()
                if not self._receiving_heartbeats:
                    logger.info('ArduSub is up')
                    self._receiving_heartbeats = True
                    self._request_msg_frequencies()

            elif msg_name == 'PARAM_VALUE':
                self._parameters[chars_to_str(mav_msg['message']['param_id'])] = mav_msg['message']['param_value']

            elif msg_name == 'NAMED_VALUE_FLOAT':
                self._named_floats[chars_to_str(mav_msg['message']['name'])] = mav_msg['message']['value']

        if self._msg_callback is not None:
            self._msg_callback(mav_msg)

    async def _ws_dispatch(self, ws):
        """
        Receive and handle websocket messages
        """
        while True:
            ws_msg = await ws.receive()

            if ws_msg.type == aiohttp.WSMsgType.TEXT:
                self._add_ws_text_msg(ws_msg)
            elif ws_msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'ws exception during receive: {ws.exception()}')
                break
            elif ws_msg.type == aiohttp.WSMsgType.CLOSED:
                logger.warning(f'ws closed by remote')
                break
            else:
                logger.error(f'ws unexpected message type: {ws_msg.type}')

    def ok(self) -> bool:
        # Use this as a timer
        if self._last_heartbeat_time is not None and time.time() - self._last_heartbeat_time > 2.0:
            logger.warning('HEARTBEAT time out')
            self._reset()

        return self._websocket_is_open and self._receiving_heartbeats

    async def open_websocket(self) -> None:
        """
        Open a websocket to mavlink2rest, and keep it open
        """
        ws_url = self._mavlink2rest_url + '/ws/mavlink?filter=.*'
        while True:
            await asyncio.sleep(1)
            async with aiohttp.ClientSession() as cs:
                try:
                    ws = await cs.ws_connect(ws_url)
                    logger.info(f'ws opened {ws_url}')
                    self._websocket_is_open = True
                    await self._ws_dispatch(ws)
                    self._reset()
                except Exception as ex:
                    logger.error(f'ws open exception: {ex}')
                self._websocket_is_open = False

    def set_msg_frequency(self, msg_id, frequency=4.0):
        """
        Set the desired message frequency
        """
        self._msg_frequencies[msg_id] = frequency

    def set_msg_callback(self, msg_callback):
        """
        Set the message callback
        """
        self._msg_callback = msg_callback

    def get_param(self, param_id: str) -> Optional[float]:
        """
        Get a parameter value. If we haven't seen it, request it and return None
        """
        if self.ok():
            if param_id in self._parameters:
                return self._parameters[param_id]
            else:
                self._request_param(param_id)
        return None

    def set_param(self, param_id: str, param_value: float):
        """
        Set a parameter value
        """
        if self.ok():
            msg = self.get_template('PARAM_SET')
            if msg is not None:
                logger.info(f'setting param {param_id} to {param_value}')
                msg['message']['target_system'] = self._target_system
                msg['message']['target_component'] = self._target_component
                msg['message']['param_id'] = str_to_chars(param_id, 16)
                msg['message']['param_value'] = param_value
                msg['message']['param_type'] = {'type': 'MAV_PARAM_TYPE_REAL32'}  # ArduSub will ignore this
                self.send_msg(f'PARAM_SET:{param_id}:{param_value}', msg)

    def get_named_float(self, name: str) -> Optional[float]:
        """
        Get a named float. If we haven't seen it, request the EXT_STAT data stream and return None
        """
        if self.ok():
            if name in self._named_floats:
                return self._named_floats[name]
            else:
                logger.warning(f'failed to get named float {name}, send REQUEST_DATA_STREAM:2 message')
                self._request_data_stream(apm2.MAV_DATA_STREAM_EXTENDED_STATUS)
        return None
