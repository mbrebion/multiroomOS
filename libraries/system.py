__author__ = 'mbrebion'

import os as osys
import subprocess
from libraries.networkUDP import NetworkUDP
import time
import shelve
import logging
import traceback


################################################################
################# Executing bash commands ######################
################################################################

def startCommand(command,output=False):
    if output==False:
        cmd=command+str(" > /dev/null 2>&1")
    else:
        cmd=command
    osys.system(cmd)

def startReturnCommand(command):
    try :
        out=subprocess.check_output(command, shell=True).decode("utf-8").split("\n")
        return out
    except subprocess.CalledProcessError as e:
        logDebug(e.output)
        logDebug("error in return command from system.py : ",time.time(), command)
        return ""

    #return subprocess.check_output(command, shell=True).split("\n")


################################################################
######################### Logging ##############################
################################################################


startCommand("cp /home/pi/os/pythonos.log /home/pi/os/saved_pythonos.log")
logging.basicConfig(filename='/home/pi/os/pythonos.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d,%H:%M:%S',filemode='w')

def log_except_hook(*exc_info):
    text = "".join(traceback.format_exception(*exc_info))
    logging.critical("Unhandled exception: %s", text)
    print(text)

def logDebug(*message):
    out=""
    for x in message:
        out += str(x) + " "
    logging.debug(out)

def logInfo(*message):
    out=""
    for x in message:
        out += str(x) + " "
    logging.info(out)

def logWarning(*message):
    out=""
    for x in message:
        out+=str(x)+" "
    logging.warning(out)

#sys.excepthook = log_except_hook
# writing of uncaught exception on log


################################################################
############## Networking : Bluetooth and wifi #################
################################################################

wifiStatus=True


def printRemainingMemory():
    out = startReturnCommand("free -h | grep \"Mem\"")
    logWarning(out)


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

def shutdownWifi():
    global wifiStatus
    if wifiStatus:

        NetworkUDP().leaveNetwork()
        logDebug("wifi down !")
        startCommand("sudo ifconfig wlan0 down")

        wifiStatus=False

def restartWifi(io=None):
    global wifiStatus
    if not wifiStatus:

        startCommand("sudo ifconfig wlan0 up")
        logDebug("wifi starting !")
        time.sleep(0.5)

        if io is not None:
            logDebug("nudp starting !")
            io.startNetwork()

        wifiStatus=True

################################################################
################# saving parameters in shelf ###################
################################################################

shelf = False

def openShelf():
    global shelf
    shelf = shelve.open("/home/pi/os/settings.shelf",writeback=True)

def getDataFromShelf(key):
    global shelf
    if key in shelf:
        return shelf[key]
    else:
        return ""

def putToShelf(key,data):
    global shelf
    shelf[key]=data
    shelf.sync()

def closeShelf():
    global shelf
    shelf.close()

##################### dealing with snapcast ####################
### these commands are usefull for server as well as clients ###
################################################################

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
    logInfo("     snapserver created")

def stopSnapServer():
    global subPSServer
    if subPSServer != False:
        subPSServer.kill()
        subPSServer=False
        logInfo("     snapserver killed")

def switchToSnapCastOutput():
    startSnapServer()
    startCommand("mpc enable 1")
    startCommand("mpc disable 2")

def switchToLocalOutput():
    startCommand("mpc enable 2")
    startCommand("mpc disable 1")
    stopSnapServer()

subPSClient = False

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
    logInfo("     snapclient created")

def stopSnapClient():
    global subPSClient
    if subPSClient != False:
        subPSClient.kill()
        subPSClient=False
        logInfo("     snapclient killed")


################################################################
###################### MPC/MPD commands ########################
################################################################

def mpcClear():
    startCommand("mpc clear")

def mpcPlay():
    startCommand("mpc play")

def mpcPause():
    startCommand("mpc pause")

def mpcStop():
    startCommand("mpc stop")

def mpcNext():
    startCommand("mpc next")

def mpcPrevious():
    startCommand("mpc prev")

def mpcUpdate():
    startCommand("mpc update")

def mpcVolume(x):
    startCommand("mpc volume "+str(x))

def isMPDPlaying():
    output = startReturnCommand("mpc")
    out=False
    for line in output:
        if "playing" in line:
            out=True
    return out

################################################################
###################### Various commands ########################
################################################################

def checkCDStatus():
    try:
        output = startReturnCommand(" /usr/bin/cdcd tracks")
        count=0
        cdName = output[count].split("name:")[1].lstrip(' ')
        count+=1


        if not cdName=="":
            cdArtist = output[count].split("artist:")[1].lstrip(' ')
            count+=1
            inDB = checkCDinDB(cdName, cdArtist)

        else:
            cdName="unknown"
            cdArtist="unknown"
            inDB=False

        tracksNB=int(output[count].split("tracks:")[1].split("Disc")[0].lstrip(' '))
        tracks=[]
        count+=4

        for i in range(tracksNB):
            tracks.append(output[count+i].split("]")[1].lstrip(' '))

        return [cdName,cdArtist,tracks,inDB]
    except:
        return False

def checkCDinDB(album,artist):
    cmd=" mpc search Album \""+ album+"\" artist  \"" +artist+"\" "
    output = startReturnCommand(cmd)
    return output[0]!=""

def shutdownPi():
    startCommand("sudo halt")

def sleep(tm):
    time.sleep(tm)

def isFile(name):
    return osys.path.isfile(name)
