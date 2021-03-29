#!/bin/sh
reconnTimeOut=15
TERM=vt100
while /bin/true
        do /bin/socat $*
        echo -e \\033c
        echo "Disconnect sensed. Reconnecting in $reconnTimeOut seconds"
        sleep $reconnTimeOut
done
