# Surftrak Fixit 

_Surftrak_ is a new flight mode in [ArduSub 4.5](https://www.ardusub.com/).

_Surftrak Fixit_ is a [BlueOS](https://docs.bluerobotics.com/ardusub-zola/software/onboard/BlueOS-1.1/overview/)
extension that can diagnose and suggest fixes for some common Surftrak problems.

## Install

To install this extension in BlueOS:
* Select _Extensions_ in the sidebar, then the _Installed_ tab
* Click on the + icon in the lower right
* Enter the following information, then click _Create_

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
v1.0.0-beta.1
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
