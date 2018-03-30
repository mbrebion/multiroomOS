__author__ = 'mbrebion'
import os as osys
import time

def startCommand(command,output=False):
    if output==False:
        cmd=command+str(" > /dev/null 2>&1")
    else:
        cmd=command
    osys.system(cmd)



def isFile(name):
    return osys.path.isfile(name)




def sleep(tm):
    time.sleep(tm)