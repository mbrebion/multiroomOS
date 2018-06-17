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
    print "           snapclient started (simple)"

def startSnapClient():
    """
    use raw output
    :return:
    """
    global subP
    FNULL = open(osys.devnull, 'w')
    subP=subprocess.Popen(['/usr/bin/snapclient', '-s 6 '],stdout=FNULL, stderr=subprocess.STDOUT)
    print "           snapclient started (complex)"


def stopSnapClient():
    global subP
    if subP != False:
        subP.kill()
        subP=False
        print "           snapclient killed"


def shutdownPi():
    startCommand("sudo halt")


def sleep(tm):
    time.sleep(tm)