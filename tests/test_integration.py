import time
import requests
import pytest

APP_URL = "http://localhost:8080"
M2R_URL = "http://localhost:8088/v1"


@pytest.fixture(scope="session", autouse=True)
def ensure_stack_running():
    """Verify that Surftrak Fixit and mavlink2rest are running."""
    max_wait = 15
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r_m2r = requests.get(f"{M2R_URL}/helper/mavlink?name=HEARTBEAT", timeout=1)
            r_app = requests.get(f"{APP_URL}/status", timeout=1)
            if r_m2r.status_code == 200 and r_app.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        pytest.fail("Dev stack is not running. Please start it with `./dev.py start` before running tests.")


def test_web_ui_and_static_files():
    """Verify that root page and static assets are served properly."""
    r_index = requests.get(f"{APP_URL}/")
    assert r_index.status_code == 200
    assert "Surftrak status" in r_index.text

    r_css = requests.get(f"{APP_URL}/css/index.css")
    assert r_css.status_code == 200
    assert "status-error" in r_css.text

    r_js = requests.get(f"{APP_URL}/js/index.js")
    assert r_js.status_code == 200
    assert "getStatus" in r_js.text


def test_status_endpoint():
    """Verify /status returns ArduSub connection state and parameters."""
    # Allow parameters to synchronize
    for _ in range(10):
        r = requests.get(f"{APP_URL}/status")
        assert r.status_code == 200
        data = r.json()
        if data.get("mav_state") == 1:
            break
        time.sleep(0.5)

    assert data.get("mav_state") == 1, f"Expected mav_state == 1 (Up), got {data.get('mav_state')}"
    assert "surftrak_depth" in data
    assert "psc_jerk_z" in data
    assert "pilot_accel_z" in data
    assert "rngfnd_sq_min" in data


def test_fake_ping_rangefinder():
    """Verify that fake Ping sonar DISTANCE_SENSOR messages are detected."""
    # Obtain template from mavlink2rest
    r_tpl = requests.get(f"{M2R_URL}/helper/mavlink?name=DISTANCE_SENSOR")
    assert r_tpl.status_code == 200
    msg = r_tpl.json()

    # Configure as Ping sonar (sys_id=1, comp_id=194, down-facing)
    msg["header"]["system_id"] = 1
    msg["header"]["component_id"] = 194
    msg["message"]["min_distance"] = 22
    msg["message"]["max_distance"] = 4444
    msg["message"]["current_distance"] = 520
    msg["message"]["mavtype"] = {"type": "MAV_DISTANCE_SENSOR_ULTRASOUND"}
    msg["message"]["orientation"] = {"type": "MAV_SENSOR_ROTATION_PITCH_270"}
    msg["message"]["signal_quality"] = 95
    msg["message"]["time_boot_ms"] = 1000

    r_post = requests.post(f"{M2R_URL}/mavlink", json=msg)
    assert r_post.status_code == 200

    # Verify /status sees ping sensor
    time.sleep(0.2)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    status_data = r_status.json()

    assert status_data.get("ping") is not None
    assert status_data["ping"]["distance"] == 520
    assert status_data["ping"]["sq"] == 95


def test_fake_wl_dvl_rangefinder():
    """Verify that fake Water Linked DVL DISTANCE_SENSOR messages are detected."""
    r_tpl = requests.get(f"{M2R_URL}/helper/mavlink?name=DISTANCE_SENSOR")
    assert r_tpl.status_code == 200
    msg = r_tpl.json()

    # Configure as WL DVL (sys_id=255, comp_id=0, down-facing)
    msg["header"]["system_id"] = 255
    msg["header"]["component_id"] = 0
    msg["message"]["min_distance"] = 22
    msg["message"]["max_distance"] = 5000
    msg["message"]["current_distance"] = 650
    msg["message"]["mavtype"] = {"type": "MAV_DISTANCE_SENSOR_LASER"}
    msg["message"]["orientation"] = {"type": "MAV_SENSOR_ROTATION_PITCH_270"}
    msg["message"]["signal_quality"] = 90
    msg["message"]["time_boot_ms"] = 1000

    r_post = requests.post(f"{M2R_URL}/mavlink", json=msg)
    assert r_post.status_code == 200

    time.sleep(0.2)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    status_data = r_status.json()

    assert status_data.get("wl_dvl") is not None
    assert status_data["wl_dvl"]["distance"] == 650
    assert status_data["wl_dvl"]["sq"] == 90


def test_fixit_bad_orient():
    """Test fixing RNGFND1_ORIENT."""
    r = requests.post(f"{APP_URL}/fixit", json={"fix": "prb_bad_orient"})
    assert r.status_code == 200

    # Wait for param to update
    time.sleep(0.5)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    data = r_status.json()
    assert data.get("rngfnd1_orient") == 25


def test_fixit_bad_max():
    """Test fixing RNGFND1_MAX_CM / RNGFND1_MAX."""
    r = requests.post(f"{APP_URL}/fixit", json={"fix": "prb_bad_max"})
    assert r.status_code == 200

    time.sleep(0.5)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    data = r_status.json()
    if data.get("vehicle_version") == "4.7":
        assert data.get("rngfnd1_max") == 50.0
    else:
        assert data.get("rngfnd1_max_cm") == 5000 or data.get("rngfnd1_max") == 5000


def test_fixit_bad_kpv():
    """Test fixing PSC_JERK_Z and PILOT_ACCEL_Z."""
    r = requests.post(f"{APP_URL}/fixit", json={"fix": "prb_bad_kpv"})
    assert r.status_code == 200

    time.sleep(0.5)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    data = r_status.json()
    assert data.get("psc_jerk_z") == 8
    assert data.get("pilot_accel_z") == 500


def test_fixit_no_btn():
    """Test fixing BTN0_FUNCTION for Surftrak."""
    r = requests.post(f"{APP_URL}/fixit", json={"fix": "prb_no_btn"})
    assert r.status_code == 200

    time.sleep(0.5)
    r_status = requests.get(f"{APP_URL}/status")
    assert r_status.status_code == 200
    data = r_status.json()
    assert data.get("btn_surftrak") == "BTN0_FUNCTION"
