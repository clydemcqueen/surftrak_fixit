# Surftrak Fixit

_Surftrak_ is a new flight mode in [ArduSub 4.5](https://www.ardusub.com/).

_Surftrak Fixit_ is a [BlueOS](https://docs.bluerobotics.com/ardusub-zola/software/onboard/BlueOS-1.1/overview/) extension that can diagnose and fix Surftrak problems.

## Install

* Select _Extensions_ in the sidebar
* Click on _Surftrak Fixit_
* Click _Install_

## Releases

### v1.0.0-beta.2

* Display DISTANCE_SENSOR messages from well-known sources
* Check for bad RNGFND1_TYPE
* Add FIX IT buttons for some problems
* UI improvements, works in dark mode

### v1.0.0-beta.1

* First version

## Developer Notes

### Install a custom version

* Select _Extensions_ in the sidebar, then the _Installed_ tab
* Click on the + icon in the lower right
* Enter the following information, modifying as necessary
* Click _Create_

_Extension Identifier_
~~~
clydemcqueen.surftrak_fixit
~~~

_Extension Name_
~~~
surftrak_fixit
~~~

_Docker image_
~~~
clydemcqueen/surftrak_fixit
~~~

_Docker tag_
~~~
v1.0.0-beta.2
~~~

_Custom settings_
~~~
{
  "ExposedPorts": {
    "8080/tcp": {}
  },
  "HostConfig": {
    "ExtraHosts": ["host.docker.internal:host-gateway"],
    "PortBindings": {
      "8080/tcp": [
        {
          "HostPort": ""
        }
      ]
    }
  },
  "Env": ["MAVLINK2REST_URL=http://host.docker.internal/mavlink2rest/v1"]
}
~~~


### Testing with ArduSub SITL

_Surftrak Fixit_ looks only at MAVLink messages, so it can be tested against ArduSub SITL and
[mavlink2rest](https://github.com/mavlink/mavlink2rest/).

See [these instructions](https://ardupilot.org/dev/docs/building-the-code.html) to set up ArduSub SITL.

Terminal 1: run SITL
~~~
cd $ARDUPILOT_HOME
mkdir run_sim
cd run_sim
nice ../Tools/autotest/sim_vehicle.py -G -D -l 47.6302,-122.3982391,-0.1,270 -v Sub -f vectored --out "127.0.0.1:14551"
~~~

Terminal 2: run mavlink2rest in a docker container
~~~
docker build --build-arg TARGET_ARCH=x86_64-unknown-linux-musl -t mavlink/mavlink2rest .
docker run --rm --init -p 8088:8088 -p 14550:14550/udp --name mavlink2rest mavlink/mavlink2rest
~~~

Terminal 3: run _Surftrak Fixit_
~~~
./main.py --mavlink2rest_url http://localhost:8088/v1
~~~

Terminal 4: emulate a MAVLink rangefinder
~~~
./fake_rf.py --ping
~~~

You can see the extension UI at http://localhost:8080/
