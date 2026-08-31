## Testing with ArduSub SITL

_Surftrak Fixit_ looks only at MAVLink messages, so it can be tested against ArduSub SITL and
[mavlink2rest](https://github.com/mavlink/mavlink2rest/).

### Automated (dev.py)

You can manage the full development and testing stack using `dev.py`:

1. **Start the test stack** (ArduSub SITL, mavlink2rest 0.11.25, and Surftrak Fixit):
~~~
export ARDUPILOT_HOME="path/to/ardupilot"
./dev.py start
~~~

2. **Check stack status and connection**:
~~~
./dev.py status
~~~

3. **Run automated integration tests**:
~~~
./dev.py test
~~~

4. **Emulate rangefinders** (optional):
~~~
./dev.py fake-rf --ping
# or
./dev.py fake-rf --wl-dvl
~~~

5. **Stop the stack**:
~~~
./dev.py stop
~~~

The extension UI is available at http://localhost:8080/

---

### Manual

Terminal 1: run SITL
~~~
cd $ARDUPILOT_HOME
mkdir -p run_sim
cd run_sim
nice ../Tools/autotest/sim_vehicle.py -N -v Sub -f vectored -l 47.6302,-122.3982391,-0.1,270 --out 127.0.0.1:14551 --no-rcin
~~~

Terminal 2: run mavlink2rest
~~~
./.venv/bin/mavlink2rest -c udpin:0.0.0.0:14550 -s 0.0.0.0:8088
~~~

Terminal 3: run _Surftrak Fixit_
~~~
./.venv/bin/python app/main.py --mavlink2rest_url http://localhost:8088/v1
~~~

Terminal 4: emulate a MAVLink rangefinder
~~~
./.venv/bin/python app/fake_rf.py --ping
~~~
