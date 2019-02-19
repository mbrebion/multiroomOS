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


def checkCDStatus():
    try:
        output = startReturnCommand(" /usr/bin/cdcd tracks")
        cdName = output[0].split("name:")[1].lstrip(' ')
        cdArtist = output[1].split("artist:")[1].lstrip(' ')
        tracksNB=int(output[2].split("tracks:")[1].split("Disc")[0].lstrip(' '))
        tracks=[]
        idec=6
        for i in range(tracksNB):
            tracks.append(output[idec+i].split("]")[1].lstrip(' '))

        inDB=checkCDinDB(cdName,cdArtist)
        return [cdName,cdArtist,tracks,inDB]
    except:
        return False


def checkCDinDB(album,artist):
    cmd=" mpc search Album \""+ album+"\" artist  \"" +artist+"\" "
    output = startReturnCommand(cmd)


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
        print("wifi down !")
        startCommand("sudo ifconfig wlan0 down")

        wifiStatus=False

def restartWifi():
    global wifiStatus
    if not wifiStatus:
        startCommand("sudo ifconfig wlan0 up")
        wifiStatus=True


def startReturnCommand(command):
    return subprocess.check_output(command, shell=True).decode("utf-8").split("\n")

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

subPSServer = False
def startSnapServer():
    """
    use raw output
    :return:
    """
    global subPSServer
    if subPSServer != False:
        stopSnapServer()

    FNULL = open(osys.devnull, 'w')
    subPSServer=subprocess.Popen(['/usr/bin/snapserver'],stdout=FNULL, stderr=subprocess.STDOUT)
    print("     snapserver created")


def stopSnapServer():
    global subPSServer
    if subPSServer != False:
        subPSServer.kill()
        subPSServer=False
        print("     snapserver killed")


def switchToSnapCastOutput():
    startSnapServer()
    startCommand("mpc enable 1")
    startCommand("mpc disable 2")


def switchToLocalOutput():
    stopSnapServer()
    startCommand("mpc enable 2")
    startCommand("mpc disable 1")


subPSClient = False
def startSnapClientSimple():
    """
    use pulse output (needed for volume control relying on hifiberry mini amp)
    :return:
    """
    global subPSClient
    if subPSClient != False:
        stopSnapClient()
    FNULL = open(osys.devnull, 'w')
    subPSClient=subprocess.Popen(['/usr/bin/snapclient', '-s 6 '],stdout=FNULL, stderr=subprocess.STDOUT)
    print("     snapclient simple created")

def startSnapClient():
    """
    use raw output
    :return:
    """
    global subPSClient
    if subPSClient != False:
        stopSnapClient()

    FNULL = open(osys.devnull, 'w')
    subPSClient=subprocess.Popen(['/usr/bin/snapclient', '-s 6 '],stdout=FNULL, stderr=subprocess.STDOUT)
    print("     snapclient created")


def stopSnapClient():
    global subPSClient
    if subPSClient != False:
        subPSClient.kill()
        subPSClient=False
        print("     snapclient killed")


def shutdownPi():
    startCommand("sudo halt")


def sleep(tm):
    time.sleep(tm)