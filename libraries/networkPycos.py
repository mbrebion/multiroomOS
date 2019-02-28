import socket,sys
import pycos
from time import sleep
import pycos.netpycos
from networkMasterPycos import STATUS_MASTER,STATUS_FOLLOWER,get_ip,GOODBYE_MASTER,GOODBYE,SYSTEM,TIMEOUT,HELLO,ASK_MASTER,COMM



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

        pycos.Pycos(node=get_ip(),name=name) # instantiate pycos with the good IP (default behaviour non working on rpis !!!)
        self.alive=True
        self.master=None
        self._receiver=pycos.Task(self._receiver)  # used for comms
        pycos.Task(self._findMaster,[]) # deals with network
        while self.master==None:
            sleep(0.1)

        pycos.Task(self._listenMaster)
        print("end of init")

    def listToString(self):
        out = ""
        for e in self.remoteDevicesSYST.keys():
            out += e + ","
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

    def masterTask(self, names,task=None):
        """

        :param names: list of already known nodes (usefull when master is created after a former master failure
        :param task:
        :return:
        """
        task.set_daemon()
        task.register(self.networkTag)
        print(" master task : " + self.networkTag)
        for name in names:
            follower = yield pycos.Task.locate(name + SYSTEM, timeout=TIMEOUT)
            if follower != None:
                self.remoteDevicesSYST[name] = follower
                follower.send(self.listToString())

        while self.alive:
            # receive message
            msgName = yield task.receive(TIMEOUT)
            if msgName==None:
                continue
            try:
                name,msg=msgName.split(",")
            except:
                print("strange mess received ",msgName)


            if msg==HELLO:
                # new (or not) remote device is saying hello
                print("received hello from ", name)
                if name!=self.name:
                    loc = yield pycos.Pycos().locate(name)
                    out = yield pycos.Pycos().peer(loc, stream_send=True)
                    follower = yield pycos.Task.locate(name + SYSTEM, location=loc, timeout=TIMEOUT * 5)
                else:
                    follower = yield pycos.Task.locate(name + SYSTEM, timeout=TIMEOUT * 5)

                if follower != None:
                    self.remoteDevicesSYST[name]=follower
                else :
                    print("could not locate "+name+SYSTEM)

            elif msg==GOODBYE  or msg==GOODBYE_MASTER:
                # remote device is saying goodbye
                del self.remoteDevicesSYST[name]



            elif msg in self.remoteDevices.keys():
                lostNode=msg
                # if a remote device advert another remote device names, we must check that it is still alive
                lostFollower = yield pycos.Task.locate(lostNode + SYSTEM, timeout=TIMEOUT)
                if lostFollower==None:
                    del self.remoteDevicesSYST[lostNode]


            for follower in self.remoteDevicesSYST.values():
                follower.send(self.listToString())

            if msg==GOODBYE_MASTER and len(self.remoteDevicesSYST)>0:
                # remote device owning master is leaving, a new one must be chosen
                v = list(self.remoteDevicesSYST.values())
                v[0].send(ASK_MASTER)



    def _findMaster(self,names,task=None):

        """
        en cas d'absence de master, ce node DEVIENT le master

        :param task: reference to pycos task associated with this coroutine
        :return:
        """

        self.master = yield pycos.Task.locate(self.networkTag,timeout=TIMEOUT)

        if self.master== None:
            # with no master, this node become master
            self.master=pycos.Task(self.masterTask,names)
            self.status=STATUS_MASTER
            print("master created")
        else:
            self.status=STATUS_FOLLOWER



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
                pycos.Task(self._findMaster,list(self.remoteDevices.keys()))

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
                    out = yield pycos.Pycos().peer(loc,stream_send=True)
                    follower = yield pycos.Task.locate(name + COMM, location=loc, timeout=TIMEOUT * 5)
                    print("update st for (" + name + "): " + str(out))
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
            del self.remoteDevices[name]
            loc = yield pycos.Pycos().locate(name)
            yield pycos.Pycos().close_peer(loc)

        if len(self.remoteDevices.keys())==1 and self.status==STATUS_FOLLOWER:
            # only us remaining : then we must start a master
            print("become master ?")
            pycos.Task(self._findMaster,list(self.remoteDevices.keys()))

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




