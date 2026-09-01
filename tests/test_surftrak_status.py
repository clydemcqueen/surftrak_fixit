import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import mav_client
from surftrak_status import SurftrakStatus, FixitModel


class TestSurftrakStatusVersionDetection(unittest.TestCase):
    def setUp(self):
        self.mock_mav = MagicMock()
        self.mock_mav.state.return_value = mav_client.MavClient.State.up
        self.mock_mav.get_named_float.return_value = None
        self.mock_mav.get_msg.return_value = None

    def test_version_4_5_detection_and_params(self):
        """Test that vehicle with RNGFND1_MIN_CM is recognized as 4.5."""
        def mock_get_param(param_id):
            params = {
                'RNGFND1_MIN_CM': 20.0,
                'RNGFND1_MAX_CM': 5000.0,
                'RNGFND1_TYPE': 10.0,
                'RNGFND1_ORIENT': 25.0,
                'SURFTRAK_DEPTH': 50.0,
                'PSC_JERK_Z': 8.0,
                'PILOT_ACCEL_Z': 500.0,
                'RNGFND_SQ_MIN': 50.0,
            }
            return params.get(param_id, None)

        self.mock_mav.get_param.side_effect = mock_get_param

        status = SurftrakStatus(self.mock_mav)
        # Mock last message times to avoid timeout errors
        status._t_global_position_int = 1e12
        status._t_rangefinder = 1e12

        status_dict = status.get_status()
        self.assertEqual(status_dict['vehicle_version'], '4.5')
        self.assertEqual(status_dict['rngfnd1_min_cm'], 20.0)
        self.assertEqual(status_dict['rngfnd1_max_cm'], 5000.0)
        self.assertEqual(status_dict['rngfnd1_min'], 20.0)
        self.assertEqual(status_dict['rngfnd1_max'], 5000.0)

        # Test prb_bad_max on 4.5
        status.post_fixit(FixitModel(fix='prb_bad_max'))
        self.mock_mav.set_param.assert_called_with('RNGFND1_MAX_CM', 5000)

    def test_version_4_7_detection_and_params(self):
        """Test that vehicle with RNGFND1_MIN is recognized as 4.7."""
        def mock_get_param(param_id):
            params = {
                'RNGFND1_MIN': 0.20,
                'RNGFND1_MAX': 50.0,
                'RNGFND1_TYPE': 10.0,
                'RNGFND1_ORIENT': 25.0,
                'SURFTRAK_DEPTH': 50.0,
                'PSC_D_JERK': 8.0,
                'PILOT_ACC_Z': 500.0,
                'RNGFND_SQ_MIN': 50.0,
            }
            return params.get(param_id, None)

        self.mock_mav.get_param.side_effect = mock_get_param

        status = SurftrakStatus(self.mock_mav)
        status._t_global_position_int = 1e12
        status._t_rangefinder = 1e12

        status_dict = status.get_status()
        self.assertEqual(status_dict['vehicle_version'], '4.7')
        self.assertIsNone(status_dict['rngfnd1_min_cm'])
        self.assertIsNone(status_dict['rngfnd1_max_cm'])
        self.assertEqual(status_dict['rngfnd1_min'], 0.20)
        self.assertEqual(status_dict['rngfnd1_max'], 50.0)
        self.assertEqual(status_dict['psc_jerk_z'], 8.0)
        self.assertEqual(status_dict['pilot_accel_z'], 500.0)

        # Test prb_bad_max on 4.7
        status.post_fixit(FixitModel(fix='prb_bad_max'))
        self.mock_mav.set_param.assert_called_with('RNGFND1_MAX', 50.0)

        # Test prb_bad_kpv on 4.7
        status.post_fixit(FixitModel(fix='prb_bad_kpv'))
        self.mock_mav.set_param.assert_any_call('PSC_D_JERK', 8)
        self.mock_mav.set_param.assert_any_call('PILOT_ACC_Z', 500)

    def test_version_unknown_when_no_param(self):
        """Test that vehicle version is None when neither parameter is returned."""
        self.mock_mav.get_param.return_value = None

        status = SurftrakStatus(self.mock_mav)
        status_dict = status.get_status()
        self.assertIsNone(status_dict['vehicle_version'])
        self.assertIsNone(status_dict['rngfnd1_min'])
        self.assertIsNone(status_dict['rngfnd1_max'])

    def test_version_reset_when_down(self):
        """Test that vehicle version is None when mav_state is down."""
        self.mock_mav.state.return_value = mav_client.MavClient.State.down

        status = SurftrakStatus(self.mock_mav)
        status_dict = status.get_status()
        self.assertIsNone(status_dict['vehicle_version'])


if __name__ == "__main__":
    unittest.main()
