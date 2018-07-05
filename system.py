__author__ = 'mbrebion'

import os as osys
import subprocess
import time
import shelve

def startCommand(command,output=False):
    if output==False:
        cmd=command+str(" > /dev/null 2>&1")
    else:
        cmd=command
    osys.system(cmd)




def checkCDinDB(album,artist):
    cmd=" mpc search Album \""+ album+"\" artist  \"" +artist+"\" "
    print cmd
    output = startReturnCommand(cmd)
    return len(output)!=0


def isBluetoothDevicePlaying():
    """
    :return: True if bluetooth device is playing, else False
    """
    out=startReturnCommand("pactl list sources | grep State")
    outSTR=""
    for st in out:
        outSTR=outSTR+st

    return ("RUNNING" in outSTR)

def killBluetoothStream():
    startCommand("pactl suspend-source 1") # this may be improved in case of multiple sources
    # this commands stop the stream receiving but not the stream itself; It means the device will still play after ths command.
    # In addition to, the device must disconnect and reconnect to stream again properly


wifiStatus=True
def shutdownWifi():
    global wifiStatus
    if wifiStatus:
        startCommand("sudo ifconfig wlan0 down")
        wifiStatus=False

def restartWifi():
    global wifiStatus
    if not wifiStatus:
        startCommand("sudo ifconfig wlan0 up")
        wifiStatus=True


def startReturnCommand(command):
    return subprocess.check_output(command, shell=True).split("\n")

def isFile(name):
    return osys.path.isfile(name)


shelf = False

def openShelf():
    global shelf
    shelf = shelve.open("/home/pi/os/settings.shelf",writeback=True)

def getDataFromShelf(key):
    global shelf
    return shelf[key]

def putToShelf(key,data):
    global shelf
    shelf[key]=data
    shelf.sync()


def closeShelf():
    global shelf
    shelf.close()

# dealing with snapcast
# these commands are usefull for server as well as clients

# server side
def switchToSnapCastOutput():
    startCommand("mpc enable 1")
    startCommand("mpc disable 2")
    startCommand("mpc volume 70")


def switchToLocalOutput():

    startCommand("mpc enable 2")
    startCommand("mpc disable 1")
    startCommand("mpc volume 70")


subP = False

def startSnapClientSimple():
    """
    use pulse output (needed for volume control relying on hifiberry mini amp)
    :return:
    """
    global subP
    FNULL = open(osys.devnull, 'w')
    subP=subprocess.Popen(['/usr/bin/snapclient', '-s 2 '],stdout=FNULL, stderr=subprocess.STDOUT)

def startSnapClient():
    """
    use raw output
    :return:
    """
    global subP
    FNULL = open(osys.devnull, 'w')
    subP=subprocess.Popen(['/usr/bin/snapclient', '-s 6 '],stdout=FNULL, stderr=subprocess.STDOUT)


def stopSnapClient():
    global subP
    if subP != False:
        subP.kill()
        subP=False
        print "     snapclient killed"


def shutdownPi():
    startCommand("sudo halt")


def sleep(tm):
    time.sleep(tm)