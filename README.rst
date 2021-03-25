GE/Caddx/NetworX NX584/NX8E Interface Library and Server
===============================================

This is a tool to let you interact with your NetworX alarm panel via
the NX584 module (which is built into NX8E panels). You must enable it
in the configuration of the control panel. 

This package is designed to be a direct replacement for pynx584.
Connection services allow for HTTP server (flask) and/or MQTT client (paho-mqtt).

MQTT provides considerable improvements in zone change latency. Also, since flask is really designed only for development and is considered unstable, HTTP usage is not suggested.


Install Locally
***************

::

 # pip3 install nx584mqtt
 
 - Package installation allows for optional requirements, based on user needs:
 
 # pip3 install nx584mqtt:full
 >> All options
 # pip3 install nx584mqtt:http
 >> Installs flask
 # pip3 install nx584mqtt:client
 >> Installs prettytable
 
 

The server must be run on a machine with connectivity to the panel,
which can be a local serial port, or a Serial-over-LAN device (i.e. a
TCP socket). For example::

 # nx584_server --serial /dev/ttyS0 --baud 38400

or::

 # nx584_server --connect 192.168.1.101:23




# Client Usage (if enabled/installed)

Once that is running, you should be able to do something like this::

 $ nx584_client summary
 +------+-----------------+--------+--------+
 | Zone |       Name      | Bypass | Status |
 +------+-----------------+--------+--------+
 |  1   |    FRONT DOOR   |   -    | False  |
 |  2   |   GARAGE DOOR   |   -    | False  |
 |  3   |     SLIDING     |   -    | False  |
 |  4   | MOTION DETECTOR |   -    | False  |
 +------+-----------------+--------+--------+
 Partition 1 armed

 # Arm for stay with auto-bypass
 $ nx584_client arm-stay

 # Arm for exit (requires tripping an entry zone)
 $ nx584_client arm-exit

 # Auto-arm (no bypass, no entry zone trip required)
 $ nx584_client arm-auto

 # Disarm
 $ nx584_client disarm --master 1234



Install Dev version
**************************

git clone https://github.com/rocket4321/nx584mqtt

cd nx584mqtt

pip3 install .


 
Install via Docker Compose
**************************
Before creating the Docker container, you need to define how you connect to the panel (local serial port, or a Serial-over-LAN device (i.e. a TCP socket)) in the :code:`docker-compose.yml` file. Uncomment and edit the :code:`environment` section to fit your needs::

 version: "3.2"

 services:
   nx584mqtt:
     container_name: nx584mqtt
     image: rocket4321/nx584mqtt
     build:
       context: .docker
       dockerfile: Dockerfile
     restart: unless-stopped
     ports:
       - 5007:5007
     environment:
       # Uncomment these as needed, depending on how you connect to the panel (via Serial or TCP Socket)
       # - SERIAL=/dev/ttyS0
       # - BAUD=38400
       # - CONNECT=192.168.1.101:23

To build the image, create the Docker container and then run it, make sure you're at the root of the checked out repo and run::

 # docker-compose up -d

You should now be able to conect to the nx584mqtt Docker container via its exposed port (default :code:`5007`).

Config
------

The `config.ini` should be generated once the controller reports the first
zone name. However, here is a full `config.ini` if you want to pre-populate
it with zone names::

 [config]
 # max_zone is the highest numbered zone you have populated
 max_zone = 5

 # Set to true if your unit sends DD/MM dates instead of MM/DD
 euro_date_format = False
 
 [email]
 fromaddr = security@foo.com
 smtphost = imap.foo.com
 
 [zones]
 # Zone names
 1 = Front Door
 2 = Garage Entry
 3 = Garage Side
 4 = Garage Back
 5 = Kitchen
