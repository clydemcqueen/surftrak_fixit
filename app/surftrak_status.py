from typing import Optional

import pydantic

import apm2
import mav_client


class StatusModel(pydantic.BaseModel):
    # Extension status
    ok: bool = pydantic.Field(default=False)

    # Errors
    prb_not_configured: bool = pydantic.Field(default=False)
    prb_no_sensor_msgs: bool = pydantic.Field(default=False)
    prb_bad_orient: bool = pydantic.Field(default=False)

    # Warnings
    prb_bad_max: bool = pydantic.Field(default=False)
    prb_bad_kpv: bool = pydantic.Field(default=False)
    prb_no_btn: bool = pydantic.Field(default=False)

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

    # Button assignments
    btn_surftrak: Optional[str] = pydantic.Field(default=None)

    # Future:
    # firmware version
    # script installed


class SurftrakStatus:
    def __init__(self, mav: mav_client.MavClient):
        self._status = StatusModel()
        self._mav = mav
        self._mav.set_msg_callback(self.msg_callback)
        self._mav.set_msg_frequency(apm2.MAVLINK_MSG_ID_RANGEFINDER)
        self._mav.set_msg_frequency(apm2.MAVLINK_MSG_ID_GLOBAL_POSITION_INT)
        self._receiving_distance_sensor_msgs = False

    def msg_callback(self, msg: any):
        sys_id = msg['header']['system_id']
        comp_id = msg['header']['component_id']
        msg_body = msg['message']
        msg_name = msg_body['type']

        # TODO handle message timeout(s)
        if sys_id == 1 and comp_id == 1:
            if msg_name == 'RANGEFINDER':
                self._status.rangefinder_m = msg_body['distance']
            elif msg_name == 'GLOBAL_POSITION_INT':
                self._status.relative_alt_m = msg_body['relative_alt'] * 0.001
        elif msg_name == 'DISTANCE_SENSOR' and msg_body['orientation'] == apm2.MAV_SENSOR_ROTATION_PITCH_270:
            self._receiving_distance_sensor_msgs = True

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

    def get_status(self) -> dict[str, any]:
        self._status.ok = self._mav.ok()

        if self._status.ok:
            # Get named floats and parameters
            self._status.rf_target_m = self._mav.get_named_float('RFTarget')
            self._status.rngfnd1_type = self._mav.get_param('RNGFND1_TYPE')
            self._status.surftrak_depth = self._mav.get_param('SURFTRAK_DEPTH')
            self._status.psc_jerk_z = self._mav.get_param('PSC_JERK_Z')
            self._status.pilot_accel_z = self._mav.get_param('PILOT_ACCEL_Z')

            # Get BTN* params and look for surftrak-related assignments
            self.scan_buttons()

            def rf_configured() -> bool:
                return self._status.rngfnd1_type is not None and self._status.rngfnd1_type != 0

            def kpv() -> float:
                """See https://github.com/clydemcqueen/ardusub_surftrak/"""
                if self._status.psc_jerk_z is None or self._status.pilot_accel_z is None:
                    return 0
                else:
                    return 50 * self._status.psc_jerk_z / self._status.pilot_accel_z

            # A rangefinder must be configured
            self._status.prb_not_configured = self._status.rngfnd1_type == 0

            # Most users will want to assign surftrak to a button
            self._status.prb_no_btn = self._status.btn_surftrak is None

            # If kpv value is > 1.0 then the sub might oscillate up/down while trying to hold range
            self._status.prb_bad_kpv = kpv() > 1.0

            if rf_configured():
                self._status.rngfnd1_max_cm = self._mav.get_param('RNGFND1_MAX_CM')
                self._status.rngfnd1_min_cm = self._mav.get_param('RNGFND1_MIN_CM')
                self._status.rngfnd1_orient = self._mav.get_param('RNGFND1_ORIENT')

                # If we are expecting DISTANCE_SENSOR messages, but we are not seeing them, then we have a problem
                self._status.prb_no_sensor_msgs = (self._status.rngfnd1_type == 10 and
                                                   not self._receiving_distance_sensor_msgs)

                # The rangefinder must point down
                self._status.prb_bad_orient = (self._status.rngfnd1_orient is not None and
                                               self._status.rngfnd1_orient != apm2.MAV_SENSOR_ROTATION_PITCH_270)

                # If RNGFND1_MAX_CM is 700 (the default) then the pilot probably forgot to configure it
                self._status.prb_bad_max = self._status.rngfnd1_max_cm == 700

        return self._status.model_dump()
