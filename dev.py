#!/usr/bin/env python3
"""
Development and test loop runner for Surftrak Fixit.

Manages the lifecycle of:
  - ArduSub SITL
  - mavlink2rest (0.11.25)
  - Surftrak Fixit (FastAPI web app)
  - Fake Rangefinder emulation
  - Automated integration test suite

BlueOS runs mavlink2rest 0.11.25. Later versions (1.0+) will require changes to this (and every other) extension.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

ROOT_DIR = Path(__file__).resolve().parent
PID_FILE = ROOT_DIR / ".dev_pids.json"
VENV_BIN = ROOT_DIR / ".venv" / "bin"
PYTHON_BIN = VENV_BIN / "python"
M2R_BIN = VENV_BIN / "mavlink2rest"
LOGS_DIR = ROOT_DIR / ".dev_logs"

DEFAULT_ARDUPILOT = Path(os.environ.get("ARDUPILOT_HOME", "error:must set ARDUPILOT_HOME"))


def ensure_mavlink2rest() -> Path:
    """Ensure mavlink2rest 0.11.25 binary exists in .venv/bin, downloading if missing."""
    if M2R_BIN.exists():
        return M2R_BIN

    import platform
    arch_map = {
        "x86_64": "x86_64-unknown-linux-musl",
        "aarch64": "aarch64-unknown-linux-musl",
        "armv7l": "armv7-unknown-linux-musleabihf",
    }
    machine = platform.machine()
    target_arch = arch_map.get(machine, "x86_64-unknown-linux-musl")
    url = f"https://github.com/mavlink/mavlink2rest/releases/download/t0.11.25/mavlink2rest-{target_arch}"

    print(f"mavlink2rest binary not found. Downloading version 0.11.25 for {machine}...")
    VENV_BIN.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, M2R_BIN)
    M2R_BIN.chmod(0o755)
    print(f"Saved mavlink2rest to {M2R_BIN}")
    return M2R_BIN


def get_env_with_mavproxy(ardupilot_home: Path) -> dict[str, str]:
    """Ensure PATH contains mavproxy.py, checking PATH, ardupilot virtualenvs, or local .venv."""
    env = os.environ.copy()
    current_path = env.get("PATH", "")

    # Check if already available in PATH
    if subprocess.run(["which", "mavproxy.py"], capture_output=True, env=env).returncode == 0:
        return env

    # Check candidate virtualenv directories relative to ARDUPILOT_HOME or local project
    candidate_dirs = [
        ardupilot_home / ".venv" / "bin",
        ardupilot_home / "venv" / "bin",
        VENV_BIN,
    ]
    for d in candidate_dirs:
        if (d / "mavproxy.py").exists():
            env["PATH"] = f"{d}:{current_path}"
            return env

    return env


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def load_pids() -> dict[str, int]:
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_pids(pids: dict[str, int]):
    PID_FILE.write_text(json.dumps(pids, indent=2))


def stop_service(name: str, pid: int):
    if is_process_running(pid):
        print(f"Stopping {name} (PID {pid})...")
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        # Wait up to 3 seconds
        for _ in range(30):
            if not is_process_running(pid):
                break
            time.sleep(0.1)
        if is_process_running(pid):
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass


def cmd_stop(args=None):
    pids = load_pids()
    if not pids:
        print("No recorded running services.")
    else:
        for name, pid in list(pids.items()):
            stop_service(name, pid)
        if PID_FILE.exists():
            PID_FILE.unlink()

    # Kill any lingering instances on default ports
    subprocess.run("fuser -k 8080/tcp 2>/dev/null || true", shell=True)
    subprocess.run("fuser -k 8088/tcp 2>/dev/null || true", shell=True)
    subprocess.run("pkill -f 'ardusub -S' 2>/dev/null || true", shell=True)
    subprocess.run("pkill -f 'mavproxy.py' 2>/dev/null || true", shell=True)
    print("All services stopped.")


def check_url(url: str, timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def cmd_status(args=None):
    pids = load_pids()
    print("=== Surftrak Fixit Dev Stack Status ===")
    services = ["sitl", "mavlink2rest", "surftrak_fixit"]
    for svc in services:
        pid = pids.get(svc)
        if pid and is_process_running(pid):
            print(f"  [{svc}]: RUNNING (PID {pid})")
        else:
            print(f"  [{svc}]: STOPPED")

    m2r_ok = check_url("http://localhost:8088/v1/helper/mavlink?name=HEARTBEAT")
    app_ok = check_url("http://localhost:8080/status")

    print(f"  mavlink2rest HTTP (port 8088): {'ONLINE' if m2r_ok else 'OFFLINE'}")
    print(f"  surftrak_fixit Web UI (port 8080): {'ONLINE' if app_ok else 'OFFLINE'}")
    if app_ok:
        try:
            with urllib.request.urlopen("http://localhost:8080/status", timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                state_str = {0: "Down", 1: "Up", 2: "Waiting for Reboot"}.get(data.get("mav_state"), "Unknown")
                print(f"  ArduSub MAVLink Connection State: {state_str}")
        except Exception:
            pass


def cmd_start(args):
    cmd_stop()

    LOGS_DIR.mkdir(exist_ok=True)
    ardupilot_home = Path(args.ardupilot_home) if args.ardupilot_home else DEFAULT_ARDUPILOT

    if not ardupilot_home.exists():
        print(f"Error: ArduPilot directory not found at {ardupilot_home}", file=sys.stderr)
        sys.exit(1)

    ensure_mavlink2rest()

    pids = {}

    # 1. Start mavlink2rest
    print("Starting mavlink2rest 0.11.25 on :8088...")
    m2r_log = open(LOGS_DIR / "mavlink2rest.log", "w")
    m2r_proc = subprocess.Popen(
        [str(M2R_BIN), "-c", "udpin:0.0.0.0:14550", "-s", "0.0.0.0:8088"],
        stdin=subprocess.DEVNULL,
        stdout=m2r_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    pids["mavlink2rest"] = m2r_proc.pid

    # 2. Start ArduSub SITL
    print(f"Starting ArduSub SITL from {ardupilot_home}...")
    run_sim_dir = ardupilot_home / "run_sim"
    run_sim_dir.mkdir(exist_ok=True)

    env = get_env_with_mavproxy(ardupilot_home)
    if subprocess.run(["which", "mavproxy.py"], capture_output=True, env=env).returncode != 0:
        print("Warning: mavproxy.py not found in PATH or ArduPilot virtualenv. sim_vehicle.py may fail.", file=sys.stderr)

    sitl_log = open(LOGS_DIR / "sitl.log", "w")
    sim_vehicle_script = ardupilot_home / "Tools" / "autotest" / "sim_vehicle.py"
    sitl_proc = subprocess.Popen(
        [
            str(sim_vehicle_script),
            "-N",
            "-v", "Sub",
            "-f", "vectored",
            "-l", "47.6302,-122.3982391,-0.1,270",
            "--out", "127.0.0.1:14551",
            "--no-rcin",
            "--mavproxy-args=--daemon --non-interactive",
        ],
        cwd=str(run_sim_dir),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=sitl_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    pids["sitl"] = sitl_proc.pid

    # 3. Start surftrak_fixit
    print("Starting Surftrak Fixit web app on :8080...")
    app_log = open(LOGS_DIR / "app.log", "w")
    app_proc = subprocess.Popen(
        [
            str(PYTHON_BIN),
            str(ROOT_DIR / "app" / "main.py"),
            "--mavlink2rest_url", "http://localhost:8088/v1",
        ],
        cwd=str(ROOT_DIR / "app"),
        stdin=subprocess.DEVNULL,
        stdout=app_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    pids["surftrak_fixit"] = app_proc.pid

    save_pids(pids)

    # Wait for services and ArduSub connection to become responsive
    print("Waiting for stack and ArduSub SITL to become ready...")
    for _ in range(30):
        time.sleep(0.5)
        if check_url("http://localhost:8088/v1/helper/mavlink?name=HEARTBEAT") and check_url("http://localhost:8080/status"):
            try:
                with urllib.request.urlopen("http://localhost:8080/status", timeout=1.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("mav_state") == 1:
                        print("\n Stack is ready and ArduSub SITL is connected!")
                        print("  Web UI:         http://localhost:8080/")
                        print("  Status API:     http://localhost:8080/status")
                        print("  mavlink2rest:   http://localhost:8088/v1")
                        return
            except Exception:
                pass

    print("\nStack started, but ArduSub connection is still initializing. Check logs in .dev_logs/")


def cmd_fake_rf(args):
    print("Starting fake rangefinder emulation...")
    cmd = [
        str(PYTHON_BIN),
        str(ROOT_DIR / "app" / "fake_rf.py"),
        "--mavlink2rest_url", args.mavlink2rest_url,
    ]
    if args.ping:
        cmd.append("--ping")
    if args.wl_dvl:
        cmd.append("--wl-dvl")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopped fake rangefinder.")


def cmd_test(args):
    print("Running automated integration tests...")
    test_args = [str(VENV_BIN / "pytest"), "-v", str(ROOT_DIR / "tests")]
    if args.pytest_args:
        test_args.extend(args.pytest_args)
    result = subprocess.run(test_args)
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Surftrak Fixit Dev Loop CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start_parser = subparsers.add_parser("start", help="Start SITL, mavlink2rest, and Surftrak Fixit")
    start_parser.add_argument("--ardupilot_home", type=str, default=str(DEFAULT_ARDUPILOT),
                               help="Path to ArduPilot Sub directory")

    # stop
    subparsers.add_parser("stop", help="Stop all running dev services")

    # status
    subparsers.add_parser("status", help="Check status of running dev stack")

    # fake-rf
    fake_parser = subparsers.add_parser("fake-rf", help="Run fake rangefinder emulation")
    fake_parser.add_argument("--ping", action="store_true", default=True, help="Emulate Ping sonar")
    fake_parser.add_argument("--wl-dvl", action="store_true", help="Emulate Water Linked DVL")
    fake_parser.add_argument("--mavlink2rest_url", type=str, default="http://localhost:8088/v1")

    # test
    test_parser = subparsers.add_parser("test", help="Run integration test suite")
    test_parser.add_argument("pytest_args", nargs="*", help="Extra arguments to pass to pytest")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "fake-rf":
        cmd_fake_rf(args)
    elif args.command == "test":
        cmd_test(args)


if __name__ == "__main__":
    main()
