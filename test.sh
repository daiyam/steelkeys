#!/bin/sh

# sudo steelkeys -m m800 -j '{"key":"1","color":"00ff00"}'

sudo steelkeys -m m800 -p disco

read -n 1 -s -r -p "Press any key to continue"

echo ''

sudo python3 ./test/tester.py
