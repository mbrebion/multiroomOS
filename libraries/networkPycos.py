import socket,sys
import pycos
from time import sleep
import os,shlex
import pycos.netpycos
from networkMasterPycos import STATUS_MASTER,STATUS_FOLLOWER,get_ip,GOODBYE_MASTER,GOODBYE,SYSTEM,TIMEOUT,HELLO,ASK_MASTER,COMM,MASTER,NEW_MASTER,ipv4_udp_multicast,MASTER_PORT

import subprocess


# first attempt to build a network of remotes with a discovery method

class Node:



    def __init__(self,name,networkTag,recepFunc=False):
        """
        node for network communication
        :param name: name of node
        :param networkTag: tag of network to connect to
        :param recepFunc: function called when message is received
        """

        def defaultRecepFunc(msg):
            print("received message : "+msg)


        self.name=name
        self.networkTag=networkTag
        self.status=STATUS_FOLLOWER

        if recepFunc==False:
            self.recepFunc=defaultRecepFunc
        else:
            self.recepFunc=recepFunc

        self.remoteDevices={} # dict containing names of devices and pycos comm tasks associated
        self.remoteDevicesSYST = {}  # dict containing names of devices and pycos system tasks associated

        pycos.Pycos(node=get_ip(),name=name,ipv4_udp_multicast=ipv4_udp_multicast) # instantiate pycos with the good IP (default behaviour non working on rpis !!!)
        self.alive=True
        self.master=None

        self._receiver=pycos.Task(self._receiver)  # used for comms
        pycos.Task(self._findMaster) # deals with network

        while self.master==None:
            sleep(0.1)

        print("start listening master")
        pycos.Task(self._listenMaster)






    def listToString(self):
        out = ""
        for e in self.remoteDevices.keys():
            out += e + " "
        return out[0:-1]



    def shutdown(self):
        if self.master!=None:
            if self.status==STATUS_MASTER:
                self.master.send(name+","+GOODBYE_MASTER)
            else:
                self.master.send(name + "," + GOODBYE)
        self.alive=False

    #########################################################################################################
    ############################################# discovering part ##########################################
    #########################################################################################################



    def _findMaster(self,task=None,masterLoc=None):

        """
        en cas d'absence de master, ce node DEVIENT le master

        :param task: reference to pycos task associated with this coroutine
        :return:
        """

        # boucle infinie,
        self.master=None
        if masterLoc==None:
            masterLoc = yield pycos.Pycos.instance().locate(self.networkTag,timeout=TIMEOUT*2)
        if masterLoc!=None:
            self.master = yield pycos.Task.locate(self.networkTag+MASTER,timeout=TIMEOUT,location=masterLoc)


        if self.master== None:

            # with no master, this node become master
            cmd=["/usr/bin/python3",__location__+"networkMasterPycos.py",self.networkTag]+list(self.remoteDevices.keys())
            print(cmd)
            subprocess.Popen(cmd)
            yield task.sleep(0.8) # wait for master to be properly instanciated
            #masterLoc = yield pycos.Pycos().locate(self.networkTag) # locate master (on same remote but in a different process)
            masterLoc=pycos.netpycos.Location(get_ip(), MASTER_PORT)
            self.master = yield pycos.Task.locate(self.networkTag + MASTER,location=masterLoc) # retrieve master task
            self.status=STATUS_MASTER
        else:
            self.status=STATUS_FOLLOWER
        print("----------------------------------------new status : "+self.status+" of "+str(masterLoc))


    def _tellMaster(self,msg,task=None):
        out=yield self.master.deliver(self.name+","+msg,timeout=TIMEOUT)
        if out==None:
            # the connexion to master is maybe
            pycos.Task(self._findMaster,self.remoteDevices.keys())


    def _listenMaster(self,task=None):
        task.set_daemon()
        # advertize first

        task.register(self.name + SYSTEM)
        print(" system task : " + self.name + SYSTEM)

        self.master.send(self.name+","+HELLO)

        # then wait for updates
        while self.alive:
            msgList = yield task.receive(TIMEOUT)
            if msgList==None:
                continue
            # two kind of messages : else an order to become the new master, else a new list of remote devices
            if ASK_MASTER in msgList:
                yield task.sleep(1)
                pycos.Task(self._findMaster)
                print("asked to become master")

            elif NEW_MASTER in msgList :
                if self.status==STATUS_FOLLOWER:
                    order,loc=msgList.split(",")
                    yield task.sleep(1)
                    masterLoc = pycos.netpycos.Location(loc.split(":")[0], loc.split(":")[1])
                    pycos.Task(self._findMaster,masterLoc)
                    print("ask to locate new master")

            else:
                pycos.Task(self._updateList, msgList.split(","))





    def _updateList(self, names=[], task=None):
        """
        construct lists of remote devices (names and coroutines)
        :param names: list of names
        :return:
        """

        for name in names:
            if not name in self.remoteDevices.keys():
                if name!=self.name:
                    loc = yield pycos.Pycos().locate(name)
                    follower = yield pycos.Task.locate(name + COMM, location=loc, timeout=TIMEOUT * 5)
                    print("update st for (" + name + "): ")
                else:
                    follower = yield pycos.Task.locate(name + COMM, timeout=TIMEOUT)  # must not fail ;-)

                if follower==None:
                    print("big problem in _updateList : ",name+COMM)

                self.remoteDevices[name] = follower

        toDelete=[]
        for name in self.remoteDevices.keys():
            if name not in names:
                toDelete.append(name)
        for name in toDelete:
            print("delete from list : "+name)
            del self.remoteDevices[name]


        print("list updated : "+str(self.remoteDevices.keys()))



    #########################################################################################################
    ############################################ communcating part ##########################################
    #########################################################################################################


    def _receiver(self, task=None):
        """
        coroutine receiving messages
        :param task:
        :return: nothing
        """
        task.set_daemon()
        task.register(self.name + COMM)
        print(" receiver task : "+self.name + COMM)
        sleep(0.1)
        while self.alive:
            # receive message
            msg = yield task.receive(TIMEOUT) # 100 ms ?
            if msg==None:
                continue

            # handle it
            self.recepFunc(msg)

    def _send(self,name,msg,task=None):
        out = yield self.remoteDevices[name].deliver(msg,timeout=TIMEOUT)
        if out==None:
            pycos.Task(self._tellMaster,name)


    # user

    def sendAll(self,msg):
        for name in self.remoteDevices.keys():
            self.sendTo(name,msg)



    def sendTo(self,name,msg):
        if not name in self.remoteDevices:
            return
        pycos.Task(self._send,name,msg)


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))+"/"

name = sys.argv[1]
node=Node(name,"pipou")

goOn=True
while goOn :
    msg=input()
    if msg=="quit":
        goOn=False
        node.shutdown()
        continue
    node.sendAll(msg)




