#!/bin/bash

cp libraries/connect.py ../hifiView/libraries/connect.py
rsync -r --exclude 'config.py' ./* pi@piMain.local:~/os/ & 
#rsync -r --exclude 'config.py' ./* pi@piBedroom.local:~/os/ & 
rsync -r --exclude 'config.py' ./* pi@piKitchen.local:~/os/ &
wait
