#!/bin/bash
cd ~
source env/bin/activate
cd /home/jetson/Documents/PKM/yolov9
python3 detect12suaraesp32.py --weights best3.pt --device 0 --source 0
