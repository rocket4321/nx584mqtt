GE/Caddx/NetworX NX584/NX8E Interface Library and Server
===============================================


![example workflow](https://github.com/rocket4321/nx584mqtt/actions/workflows/publish-to-test-pypi.yml/badge.svg)

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)

[![GitHub release](https://img.shields.io/github/release/Naereen/StrapDown.js.svg)](https://GitHub.com/Naereen/StrapDown.js/releases/)

[![PyPI version fury.io](https://badge.fury.io/py/nx584mqtt.svg)](https://pypi.python.org/pypi/nx584mqtt/)
[![PyPI download total](https://img.shields.io/pypi/dt/nx584mqtt.svg)](https://pypi.python.org/pypi/nx584mqtt/)

[![GitHub issues](https://img.shields.io/github/issues/Naereen/StrapDown.js.svg)](https://GitHub.com/Naereen/StrapDown.js/issues/)
[![Known Vulnerabilities](https://snyk.io/test/github/rocket4321/nx584mqtt/badge.svg)](https://snyk.io/test/github/rocket4321/nx584mqtt)
[![GitHub commits](https://img.shields.io/github/commits-since/Naereen/StrapDown.js/v1.0.0.svg)](https://GitHub.com/Naereen/StrapDown.js/commit/)

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

This is a tool to let you interact with your NetworX alarm panel via
the NX584 module (which is built into NX8E panels). You must enable it
in the configuration of the control panel. 

This package is designed to be a direct replacement for pynx584.
Connection services allow for HTTP server (flask) and/or MQTT client (paho-mqtt).

MQTT provides considerable improvements in zone change latency. Also, since flask is really designed only for development and is considered unstable, HTTP usage is not suggested, but only is provided for backwards-compability.

Improvements:

- Greatly reduced latency for zone and alarm status changes
- Allows for update of alarm time on user request (not just at startup)
- Enhanced security protocol options
- User access to zone and partition flags
- Heartbeat to verify alarm connection is still active


>> Insert mqtt explorer image
