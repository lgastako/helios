#!/bin/bash

CLIENT=mongo
#CLIENT=urllib
#CLIENT=pycurl

PYTHON=/pluto/local/bin/python

export PYTHONPATH=/home/john/src/helios/clients/python
la1=`cat /proc/loadavg | awk '{print $1}'`
la5=`cat /proc/loadavg | awk '{print $2}'`
la10=`cat /proc/loadavg | awk '{print $3}'`
${PYTHON} -m helios_${CLIENT} "load_avg" "{\"la1\":\"${la11}\", \"la5\":\"${la5}\", \"la10\": \"${la10}\"}"
