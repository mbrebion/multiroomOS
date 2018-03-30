#!/bin/bash

rsync -r --exclude 'config.py' ./* pi@192.168.0.17:~/os/ 
rsync -r --exclude 'config.py' ./* pi@192.168.0.12:~/os/ 
