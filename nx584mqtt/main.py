import argparse
import logging
import logging.handlers
import os
import sys
import threading
import time

from nx584mqtt import api_alt
from nx584mqtt import api
from nx584mqtt import controller
from nx584mqtt import mqtt_client

VERSION = "1.0.2021.03.25"
DEFAULT_MQTT_PORT = 1883

LOG_FORMAT = '%(asctime)-15s %(module)s %(levelname)s %(message)s'


class NoFlaskInfoFilter(logging.Filter):
    # Matches Flask log lines for filtering
    def filter(record):
        return not ( record.levelname in ('INFO') 
                and record.module in ('_internal')
               )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.ini',
                        metavar='FILE',
                        help='Path to config file')
    # Logging
    parser.add_argument('--debug', default=False, action='store_true',
                        help='Enable debug')
    parser.add_argument('--log', default=None,
                        metavar='FILE',
                        help='Path to log file')
    levels = ('DEBUG', 'INFO', 'WARNING')
    parser.add_argument('--logLevel', default='INFO', choices=levels,
                        metavar='LOG_LEVEL_CONSOLE',
                        help='Level of log displayed to console')

    # Alarm connection
    parser.add_argument('--connect', default=None,
                        metavar='HOST:PORT',
                        help='Host and port to connect for serial stream')
    parser.add_argument('--serial', default=None,
                        metavar='PORT',
                        help='Serial port to open for stream')
    parser.add_argument('--baudrate', default=38400, type=int,
                        metavar='BAUD',
                        help='Serial baudrate')

    # Web / SSE
    # Optional
    parser.add_argument('--listen', default=None,
                        metavar='ADDR',
                        help='Listen address (defaults to None)')
    parser.add_argument('--port', default=5007, type=int,
                        help='Listen port (defaults to 5007)')

    # MQTT (Required for activation)
    parser.add_argument('--mqtt', default=None,
                        metavar='MQTT_HOST',
                        help='MQTT Client Host to connect')
    # Optional
    parser.add_argument('--mqttPort', default=DEFAULT_MQTT_PORT,
                        metavar='MQTT_PORT',
                        help='MQTT client Port (default: %s)' % DEFAULT_MQTT_PORT )
    parser.add_argument('--username', default=None,
                        metavar='MQTT_USERNAME',
                        help='MQTT Client Username')
    parser.add_argument('--password', default=None,
                        metavar='MQTT_PASSWORD',
                        help='MQTT Client Password')
    parser.add_argument('--stateTopicRoot', default='home/alarm',
                        metavar='STATE_TOPIC_ROOT',
                        help='Root topic for MQTT Client publishing')
    parser.add_argument('--commandTopic', default='home/alarm/set',
                        metavar='COMMAND_TOPIC',
                        help='Command topic for MQTT Client subscription/monitoring')
    parser.add_argument('--mqttTlsActive', default=False, action='store_true',
                        help='Enable MQTT TLS')
    parser.add_argument('--mqttTlsInsecure', default=False, action='store_true',
                        help='Ignore MQTT TLS Insecurities (Not Recommended)')
    parser.add_argument('--timeout', default=10, type=int,
                        metavar='MQTT_TIMEOUT',
                        help='MQTT Timeout in seconds')

    LOG = logging.getLogger()
    formatter = logging.Formatter(LOG_FORMAT)
    istty = os.isatty(0)

    LOG.debug("Parsing args...")
    args = parser.parse_args()

    if args.debug and not istty:
        debug_handler = logging.handlers.RotatingFileHandler(
            'debug.log',
            maxBytes=1024*1024*10,
            backupCount=3)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        LOG.addHandler(debug_handler)

    if istty:
        verbose_handler = logging.StreamHandler()
        verbose_handler.setFormatter(formatter)
        verbose_handler.setLevel(args.debug and logging.DEBUG or logging.INFO)
        LOG.addHandler(verbose_handler)

    if args.log:
        log_handler = logging.handlers.RotatingFileHandler(
            args.log,
            maxBytes=1024*1024*10,
            backupCount=3)
        log_handler.setFormatter(formatter)
        log_handler.setLevel(logging.INFO)
        LOG.addHandler(log_handler)

    if args.logLevel == 'DEBUG':
        LOG.setLevel(logging.DEBUG)
    elif args.logLevel == 'INFO':
        LOG.setLevel(logging.INFO)
    elif args.logLevel == 'WARNING':
        LOG.setLevel(logging.WARNING)
        logger = logging.getLogger()
        for handler in logger.handlers:
            handler.addFilter(NoFlaskInfoFilter)
    else:
        LOG.error('Input Log level INVALID. Try: "INFO|DEBUG|WARNING"')
        LOG.setLevel(logging.WARNING)

    if args.mqtt:
        mqtt_host = args.mqtt
        mqtt_port = args.mqttPort
        if args.username:
            mqtt_username = args.username
        else:
            mqtt_username = None
        if args.password:
            mqtt_password = args.password
        else:
            mqtt_password = None
        state_topic_root = args.stateTopicRoot
        command_topic = args.commandTopic
        tls_active = args.mqttTlsActive
        tls_insecure = args.mqttTlsInsecure
        mqtt_timeout = args.timeout

    else:
        mqtt_host = None
        mqtt_port = None
        mqtt_username = None
        mqtt_password = None
        tls_active = None
        tls_insecure = None
        mqtt_timeout = None
        state_topic_root = None
        command_topic = None

    LOG.debug('Activating controller')
    if args.connect:
        host, port = args.connect.split(':')
        ctrl = controller.NXController((host, int(port)),
                                args.config,mqtt_host, mqtt_port, mqtt_username,
				mqtt_password, state_topic_root, command_topic,
				tls_active, tls_insecure, mqtt_timeout)
    elif args.serial:
        ctrl = controller.NXController((args.serial, args.baudrate),
                                args.config,mqtt_host, mqtt_port, mqtt_username,
				mqtt_password, state_topic_root, command_topic,
				tls_active, tls_insecure, mqtt_timeout)
    else:
        LOG.error('Either host:port or serial and baudrate are required')
        return

    t = threading.Thread(target=ctrl.controller_loop)
    t.daemon = True
    t.start()

    LOG.debug('Activating services')
    try:
        LOG.info('Starting nx584mqtt %s' % VERSION)
        if args.listen:
            api.CONTROLLER = ctrl
            api_alt.CONTROLLER = ctrl
            # Blocking call
            api.app.run(debug=False, host=args.listen, port=args.port, threaded=True)
        else:
            # MQTT Only
            api_alt.CONTROLLER = ctrl

            # Exit if not connected and synced within 60 seconds (12 * 5)
# FUTURE: Make this input parm
            count = 12
            initial_mqtt_client_publish_online = False
            while (api_alt.CONTROLLER.running):
                time.sleep(5)
                if (api_alt.CONTROLLER.mqtt_client.connected == False):
                    LOG.debug('Count down to exit %s - %s' % ( int(count), api_alt.CONTROLLER.queue_active) )
                    count -= 1
                if (initial_mqtt_client_publish_online == False) and (api_alt.CONTROLLER.queue_active == False) and (api_alt.CONTROLLER.initial_mqtt_publish_all_completed): 
                    initial_mqtt_client_publish_online = True
                    topic = state_topic_root + "/system/avail"
                    api_alt.CONTROLLER.mqtt_client.publish(topic, "online", retain=True)
                if (count < 1):
                    api_alt.CONTROLLER.running = False
    except Exception as ex:
        print('Fatal: %s' % str(ex) )
    finally:
        # MQTT LWT - Mark system and zones as offline
        try:
            if args.mqtt is not None:
                topic = state_topic_root + "/system/avail"
                api_alt.CONTROLLER.mqtt_client.publish(topic, "offline", retain=True)
        except Exception as ex:
            LOG.error('Unable to send MQTT Last Will message: %s' % str(ex) )
        sys.exit()

