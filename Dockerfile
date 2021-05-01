FROM alpine:latest

RUN apk update && apk add \
      python3 py3-pip

RUN pip3 install --upgrade pip

EXPOSE 5007

# Install 
# OPTION A - Published version
#RUN pip3 install nx584mqtt
#This should allow for install of mqtt requirements
#RUN pip3 install nx584mqtt[full]

# OPTION B - DEV version
RUN pip3 install paho-mqtt
RUN pip3 install flask
WORKDIR /usr/src
COPY . .
WORKDIR /usr/src/nx584mqtt
RUN pip3 install . --use-feature=in-tree-build
RUN chmod a+x /usr/bin/nx584_server

WORKDIR /usr/src/app
COPY config.ini .

# Verify python installation
RUN which python3

# Verify package installation location
RUN find / -iname "nx584*"
# alpine:
# /usr/bin/nx584_server
# python3:
# /usr/local/bin/nx584_server

# Info
RUN /usr/bin/nx584_server --version
RUN /usr/bin/nx584_server --help

# Adjust as required
ENTRYPOINT  python3 /usr/bin/nx584_server --listen "127.0.0.1" --port 0 --logLevel "WARNING" --stateTopicRoot "tele/nx584" --commandTopic "cmnd/nx584/action" --timeout 10 --username "user" --password "secure" --mqtt "192.168.2.8" --serial /dev/ttyS0 --baud 38400 --config /usr/src/app/config.ini
