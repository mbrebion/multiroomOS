#!/bin/bash

rsync -r ./* pi@192.168.0.14:~/os/ 
#rsync -r ./* pi@192.168.0.18:~/os/ &
