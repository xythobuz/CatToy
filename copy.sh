#!/bin/bash

PORT=/dev/ttyACM1

if [ $# -ne 0 ] ; then
cat << EOF | rshell -p $PORT
cp config.py /pyboard
cp servo.py /pyboard
cp toy.py /pyboard
cp wifi.py /pyboard
cp $1 /pyboard/main.py
EOF
else
cat << EOF | rshell -p $PORT
cp config.py /pyboard
cp servo.py /pyboard
cp toy.py /pyboard
cp wifi.py /pyboard
cp CatToy.py /pyboard
EOF
fi
