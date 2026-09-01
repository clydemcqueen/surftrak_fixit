# Surftrak Fixit

_Surftrak_ is a new flight mode in [ArduSub 4.5](https://www.ardusub.com/).

_Surftrak Fixit_ is a [BlueOS](https://docs.bluerobotics.com/ardusub-zola/software/onboard/BlueOS-1.1/overview/) extension that can diagnose and fix Surftrak problems.

## Install

* Select _Extensions_ in the sidebar
* Click on _Surftrak Fixit_
* Click _Install_

## Releases

### v1.1.0-beta.1

* Bug fix: prb_bad_max should update RNGFND1_MAX_CM, not RNGFND1_ORIENT
* Support ArduSub 4.7

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

### Testing and deployment

* See [testing.md](testing.md) for local testing instructions with ArduSub SITL and mavlink2rest.
* See [deploy.md](deploy.md) for multi-architecture building, testing on Raspberry Pi, and BlueOS registry deployment instructions.
