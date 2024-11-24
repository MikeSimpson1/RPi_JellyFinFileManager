#!/bin/bash
cd /home/mike/RPi_JellyFinFileManager
/usr/bin/git pull
sudo /usr/bin/python -m flask run --host=0.0.0.0 --port=80