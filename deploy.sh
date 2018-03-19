#!/bin/bash

#rsync -r --exclude 'config.py' ./* pi@192.168.0.30:~/os/ 
rsync -r --exclude 'config.py' ./* pi@192.168.0.10:~/os/ 
