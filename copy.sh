#!/bin/bash

if [ $# -ne 0 ] ; then
cat << EOF | rshell
cp config.py /pyboard
cp log.py /pyboard
cp servo.py /pyboard
cp toy.py /pyboard
cp wifi.py /pyboard
cp $1 /pyboard/main.py
EOF
else
cat << EOF | rshell
cp config.py /pyboard
cp log.py /pyboard
cp servo.py /pyboard
cp toy.py /pyboard
cp wifi.py /pyboard
cp CatToy.py /pyboard
EOF
fi
