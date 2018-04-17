__author__ = 'mbrebion'

import os as osys
import subprocess
import time

def startCommand(command,output=False):
    if output==False:
        cmd=command+str(" > /dev/null 2>&1")
    else:
        cmd=command
    osys.system(cmd)



def isFile(name):
    return osys.path.isfile(name)




# dealing with snapcast
# these commands are usefull for server as well as clients

# server side
def switchToSnapCastOutput():
    startCommand("mpc volume 40")
    startCommand("mpc enable 1")
    startCommand("mpc disable 2")
    startCommand("mpc volume 40")


def switchToLocalOutput():
    startCommand("mpc volume 70")
    startCommand("mpc enable 2")
    startCommand("mpc disable 1")
    startCommand("mpc volume 70")


subP = False

def startSnapClient():
    global subP
    subP=subprocess.Popen(['/usr/bin/snapclient', '-s 7'])
    print "           snapclient started"


def stopSnapClient():
    global subP
    if subP != False:
        subP.kill()
        subP=False
        print "           snapclient killed"




def sleep(tm):
    time.sleep(tm)