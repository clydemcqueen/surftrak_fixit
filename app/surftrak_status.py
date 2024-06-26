import time
from typing import Optional

import pydantic
from loguru import logger

import apm2
import mav_client

MSG_TIMEOUT = 1.0


class SensorModel(pydantic.BaseModel):
    distance: float = pydantic.Field(default=0.0)
    sq: int = pydantic.Field(default=0)


class StatusModel(pydantic.BaseModel):
    # MavClient state
    mav_state: mav_client.MavClient.State = pydantic.Field(default=mav_client.MavClient.State.down)
    reboot_required: bool = pydantic.Field(default=False)

    # Sensors that send DISTANCE_SENSOR messages
    ping: Optional[SensorModel] = pydantic.Field(default=None)
    wl_dvl: Optional[SensorModel] = pydantic.Field(default=None)

    # Errors
    prb_rangefinder_timeout: bool = pydantic.Field(default=False)
    prb_global_position_int_timeout: bool = pydantic.Field(default=False)

    # From GLOBAL_POSITION_INT
    # Convert all distances to meters ("_m")
    relative_alt_m: Optional[float] = pydantic.Field(default=None)

    # From NAMED_VALUE_FLOAT
    rf_target_m: Optional[float] = pydantic.Field(default=None)

    # From RANGEFINDER
    rangefinder_m: Optional[float] = pydantic.Field(default=None)

    # Parameters
    # Assume all parameters are floats
    # Assume that RNGFND1 is dedicated to surftrak
    rngfnd1_type: Optional[float] = pydantic.Field(default=None)
    rngfnd1_max_cm: Optional[float] = pydantic.Field(default=None)
    rngfnd1_min_cm: Optional[float] = pydantic.Field(default=None)
    rngfnd1_orient: Optional[float] = pydantic.Field(default=None)
    surftrak_depth: Optional[float] = pydantic.Field(default=None)
    psc_jerk_z: Optional[float] = pydantic.Field(default=None)
    pilot_accel_z: Optional[float] = pydantic.Field(default=None)
    rngfnd_sq_min: Optional[float] = pydantic.Field(default=None)

    # Button assignments
    btn_surftrak: Optional[str] = pydantic.Field(default=None)

    # Future:
    # firmware version
    # script installed


class FixitModel(pydantic.BaseModel):
    fix: str = pydantic.Field(default='')


class SurftrakStatus:
    def __init__(self, mav: mav_client.MavClient):
        self._status = StatusModel()
        self._mav = mav
        self._mav.set_msg_callback(self.msg_callback)
        self._mav.set_msg_frequency(apm2.MAVLINK_MSG_ID_RANGEFINDER)
        self._mav.set_msg_frequency(apm2.MAVLINK_MSG_ID_GLOBAL_POSITION_INT)
        self._t_global_position_int: Optional[float] = None
        self._t_rangefinder: Optional[float] = None

    def msg_callback(self, msg: any):
        sys_id = msg['header']['system_id']
        comp_id = msg['header']['component_id']
        msg_body = msg['message']
        msg_name = msg_body['type']

        if sys_id == 1 and comp_id == 1:
            if msg_name == 'RANGEFINDER':
                self._status.rangefinder_m = msg_body['distance']
                self._t_rangefinder = time.time()
            elif msg_name == 'GLOBAL_POSITION_INT':
                self._status.relative_alt_m = msg_body['relative_alt'] * 0.001
                self._t_global_position_int = time.time()

    def scan_buttons(self):
        """
        Look at all 64 (!) BTN params and look for one tied to joystick function 13 (surftrak)
        """
        if self._status.btn_surftrak is not None:
            param_value = self._mav.get_param(self._status.btn_surftrak)
            if param_value == 13:
                # No change
                return
            else:
                # No longer assigned, scan for a new assignment
                self._status.btn_surftrak = None

        for i in range(32):
            param_id = f'BTN{i}_FUNCTION'
            param_value = self._mav.get_param(param_id)
            if param_value == 13:
                self._status.btn_surftrak = param_id
                return

            param_id = f'BTN{i}_SFUNCTION'
            param_value = self._mav.get_param(param_id)
            if param_value == 13:
                self._status.btn_surftrak = param_id
                return

    def get_distance_sensor_msg(self, sys_id: int, comp_id: int) -> Optional[SensorModel]:
        """
        Look for a down-facing DISTANCE_SENSOR msg from (sys_id, comp_id)
        """
        msg = self._mav.get_msg('DISTANCE_SENSOR', sys_id, comp_id, MSG_TIMEOUT)
        if msg is not None and msg['message']['orientation']['type'] == 'MAV_SENSOR_ROTATION_PITCH_270':
            return SensorModel(distance=msg['message']['current_distance'], sq=msg['message']['signal_quality'])
        else:
            return None

    def get_status(self) -> dict[str, any]:
        # Manage timeouts for websocket messages
        self._status.prb_global_position_int_timeout = (
                self._t_global_position_int is None or
                time.time() - self._t_global_position_int > MSG_TIMEOUT)
        self._status.prb_rangefinder_timeout = (
                self._t_rangefinder is None or
                time.time() - self._t_rangefinder > MSG_TIMEOUT)

        self._status.mav_state = self._mav.state()

        if self._status.mav_state == mav_client.MavClient.State.up:
            # Get named floats and parameters
            self._status.rf_target_m = self._mav.get_named_float('RFTarget')
            self._status.rngfnd1_type = self._mav.get_param('RNGFND1_TYPE')
            self._status.surftrak_depth = self._mav.get_param('SURFTRAK_DEPTH')
            self._status.psc_jerk_z = self._mav.get_param('PSC_JERK_Z')
            self._status.pilot_accel_z = self._mav.get_param('PILOT_ACCEL_Z')
            self._status.rngfnd_sq_min = self._mav.get_param('RNGFND_SQ_MIN')

            # Get BTN* params and look for surftrak-related assignments
            self.scan_buttons()

            # DISTANCE_SENSOR messages sent via mavlink2rest will not appear on the socket
            # https://github.com/mavlink/mavlink2rest/issues/93
            self._status.ping = self.get_distance_sensor_msg(1, 194)
            self._status.wl_dvl = self.get_distance_sensor_msg(255, 0)

            # Proposed WL DVL comp id: https://github.com/bluerobotics/BlueOS-Water-Linked-DVL/pull/31
            if self._status.wl_dvl is None:
                self._status.wl_dvl = self.get_distance_sensor_msg(0, 197)

            if self._status.rngfnd1_type is not None and self._status.rngfnd1_type != 0:
                self._status.rngfnd1_max_cm = self._mav.get_param('RNGFND1_MAX_CM')
                self._status.rngfnd1_min_cm = self._mav.get_param('RNGFND1_MIN_CM')
                self._status.rngfnd1_orient = self._mav.get_param('RNGFND1_ORIENT')
            else:
                self._status.relative_alt_m = None
                self._status.rangefinder_m = None

        return self._status.model_dump()

    def post_fixit(self, fixit: FixitModel):
        if fixit.fix == 'prb_bad_type':
            logger.info(f'fix {fixit.fix} by setting RNGFND1_TYPE to 10')
            self._mav.set_param('RNGFND1_TYPE', 10)
            self._status.reboot_required = True
        elif fixit.fix == 'prb_bad_orient':
            logger.info(f'fix {fixit.fix} by setting RNGFND1_ORIENT to 25')
            self._mav.set_param('RNGFND1_ORIENT', 25)
        elif fixit.fix == 'prb_bad_max':
            logger.info(f'fix {fixit.fix} by setting RNGFND1_MAX_CM to 5000')
            self._mav.set_param('RNGFND1_ORIENT', 5000)
        elif fixit.fix == 'prb_bad_kpv':
            logger.info(f'fix {fixit.fix} by PSC_JERK_Z to 8 and PILOT_ACCEL_Z to 500')
            self._mav.set_param('PSC_JERK_Z', 8)
            self._mav.set_param('PILOT_ACCEL_Z', 500)
        elif fixit.fix == 'prb_no_btn':
            logger.info(f'fix {fixit.fix} by setting BTN0_FUNCTION to 13')
            self._mav.set_param('BTN0_FUNCTION', 13)
        elif fixit.fix == 'reboot':
            if self._mav.reboot():
                self._status.reboot_required = False
        else:
            logger.error(f'unrecognized fix {fixit}')
