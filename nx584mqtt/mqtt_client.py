
import atexit
import datetime
import json
import logging
import paho.mqtt.client as mqtt
import ssl

from nx584mqtt import api_alt
from nx584mqtt import api

LOG = logging.getLogger('mqtt_client')

class MQTTClient(object):
    def __init__(self, host, port, username, password
		, state_topic_root, command_topic, tls_active
		, tls_insecure, timeout_sec):
        LOG.info('MQTT Client %s' % host )
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._state_topic_root = state_topic_root
        self._command_topic = command_topic
        self._tls_active = tls_active
        self._tls_insecure = tls_insecure
        self._timeout = timeout_sec
        self._dt_sync_counter = 0
        self.client = None
        self.connected = False
        self.connect()

        def publishLWT():
            topic = self._state_topic_root + "/system/avail"
            try:
               self.client.publish(topic, payload="offline", qos=1, retain=True)
               LOG.warning("MQTT disconnection normal...")
            except:
               LOG.fatal("MQTT abnormal disconnection; Last will message not sent. ")

        # Publish Last Will if we can at abnormal program termination
        atexit.register(publishLWT)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            LOG.debug('Connected with result code %s' % str(rc))

            # Mark system and zones as invalid until data is synced
            topic = self._state_topic_root + "/system/avail"
            client.publish(topic, "offline", retain=True)

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe(self._command_topic)

            # Set Last Will message, in case we disconnect not called properly
            topic = self._state_topic_root + "/system/avail"
            client.will_set(topic, payload="offline", qos=1, retain=True)

            self.connected = True
        else:
            LOG.error('MQTT connect failure %s' % str(rc))

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        payload = msg.payload.lower().decode('utf-8')
        LOG.debug('Message %s' % str(msg.payload))
        if api_alt.CONTROLLER is None:
            LOG.error('api_alt ctrl not connected.')
            return
        if payload.lower().startswith("arm_away"):
            if api_alt.CONTROLLER is not None:
                fields = payload.split(",",3) 
                api_alt.CONTROLLER.arm_exit(int(fields[1]))
                # Publish template cmd to command topic to clear code
                client.publish(self._command_topic, "nop", retain=True)
        elif payload.lower().startswith("arm_home"):
            if api_alt.CONTROLLER is not None:
                fields = payload.split(",",3) 
                api_alt.CONTROLLER.arm_stay(int(fields[1]))
                # Publish template cmd to command topic to clear code
                client.publish(self._command_topic, "nop", retain=True)
        elif payload.lower().startswith("disarm"):
            if api_alt.CONTROLLER is not None:
                fields = payload.split(",",3) 
                api_alt.CONTROLLER.disarm(fields[2],int(fields[1]))
                # Publish template cmd to command topic to clear code
                client.publish(self._command_topic, "nop", retain=True)
        elif payload.lower() == "time":
            if api_alt.CONTROLLER is not None:
                api_alt.CONTROLLER.set_time()
        elif payload.lower() == "status":
            if api_alt.CONTROLLER is not None:
                api_alt.CONTROLLER.publish_all()
        elif payload.lower() == "nop":
                pass
        else:
            LOG.error("Unknown command: '%s'" % payload.lower())

    # The callback for when the client disconnects from the server.
    def on_disconnect(self, client, userdata, rc):
        self.connected = False

    def publish(self, topic, msg=None, qos=0, retain=False):
        if self.connected:
            try:
                LOG.debug('MQTT Client Publish "%s" to "%s"' % (str(msg),topic) )
                self.client.publish(topic, msg, qos, retain)
            except Exception as ex:
                LOG.error('Unable to publish to %s: %s' % (self._host, ex))
        else:
            LOG.error('Not connected yet, missed publish to %s' % self._host)

    def publish_partition_state(self, partition, msg=None, qos=0, retain=True):
        topic = self._state_topic_root + "/partitions/" + str(partition) + "/state"
        self.publish(topic, msg, qos, retain)

    def publish_partition_condition_flags(self, partition, list=None, qos=0, retain=True):
        topic = self._state_topic_root + "/partitions/" + str(partition) + "/conditions"
        flags = str(list)
        self.publish(topic, flags, qos, retain)

    def publish_zone_state(self, zone, msg=None, qos=0, retain=True):
        topic = self._state_topic_root + "/zones/" + str(zone) + "/faulted"
        self.publish(topic, msg, qos, retain)

    def publish_zone_bypassed(self, zone, msg=None, qos=0, retain=True):
        topic = self._state_topic_root + "/zones/" + str(zone) + "/bypassed"
        self.publish(topic, msg, qos, retain)

    def publish_zone_type_flags(self, zone, list=None, qos=0, retain=True):
        topic = self._state_topic_root + "/zones/" + str(zone) + "/types"
        flags = str(list)
        self.publish(topic, flags, qos, retain)

    def publish_zone_condition_flags(self, zone, list=None, qos=0, retain=True):
        topic = self._state_topic_root + "/zones/" + str(zone) + "/conditions"
        flags = str(list)
        self.publish(topic, flags, qos, retain)

    def publish_system_datetime(self, qos=0, retain=True):
        now = datetime.datetime.now()
        self.publish(self._state_topic_root + "/system/datetime"
                    , str(now.strftime("%m/%d/%Y, %H:%M:%S"))
                    , retain=False)
        # Verify controller is still connected.
        if api_alt.CONTROLLER is None:
            LOG.error('Controller not connected.')
        # When flask active, avail flag needs to be set online after 2 publish events
        if self._dt_sync_counter < 4:
            self._dt_sync_counter += 1
# FUTURE: User with large zone count or slow connect may need to adjust this value
        if self._dt_sync_counter == 3:
            self._dt_sync_counter += 1
            topic = self._state_topic_root + "/system/avail"
            self.publish(topic, "online", retain=True)

    def connect(self):
        client = mqtt.Client()

        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        
        # Set reconnection time (60 seconds)
        client.reconnect_delay_set(60)       

        if self._username is not None:
            LOG.debug('MQTT Client connecting with username %s', self._username ) 
            client.username_pw_set(self._username, self._password)

        if self._tls_active:
            context = ssl.create_default_context()
            client.tls_set_context(context)
            if self._tls_insecure:
                client.tls_insecure_set(True)
                LOG.warning('MQTT TLS insecure is active...This is not advised.') 
            else:
                client.tls_insecure_set(False)

        try:
            LOG.debug('MQTT Client connecting to host %s at port %s' 
		% ( self._host, self._port ) )
            # Connect to mqtt server
            client.connect(self._host, int(self._port), int(self._timeout))

            # Implements a threaded interface to the network loop
            client.loop_start()

            # Publish template cmd to command topic
            client.publish(self._command_topic, "nop", retain=True)

            self.client = client
        except Exception as ex:
            LOG.error('Unable to connect to %s: %s' % (self._host, ex))

        LOG.debug('MQTT Client completed..') 
        

