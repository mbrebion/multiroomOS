import socket,sys
import pycos
from time import sleep
import pycos.netpycos


# usefull constants

TIMEOUT=2
STATUS_MASTER=1
STATUS_FOLLOWER=2

SHOW_ALL="showAll"
HELLO="hello" # message send when first connecting to master
GOODBYE="goodbye" # message send when leaving network
GOODBYE_MASTER="goodbye_master" # message send when master node leaving network
ASK_MASTER="ask_master"
SYSTEM= "_system"

COMM="_comm"


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def listToString(self):
        out=""
        for e in self.remoteDevicesSYST.keys():
            out+=e+","
        return out[0:-1]


def masterTask(networkTag,names, task=None):
    """

    :param names: list of already known nodes (usefull when master is created after a former master failure
    :param task:
    :return:
    """
    task.set_daemon()  # is it to keep ????
    task.register(networkTag)
    alive=True

    print(" master task : " + networkTag)
    remoteDevicesSYST = {}
    for name in names:
        loc = yield pycos.Pycos().locate(name)
        #out = yield pycos.Pycos().peer(loc, stream_send=True)
        follower = yield pycos.Task.locate(name + SYSTEM,location=loc, timeout=TIMEOUT)
        if follower != None:
            remoteDevicesSYST[name] = follower
            follower.send(listToString()) ################################################ to be adapted

    while alive:
        # receive message
        msgName = yield task.receive(TIMEOUT)
        if msgName == None:
            continue
        try:
            name, msg = msgName.split(",")
        except:
            print("strange mess received ", msgName)

        # messages kind : HELLO tag , GOODBYE tag or existing name

        if msg == HELLO:
            # new (or not) remote device is saying hello
            print("received hello from ", name)

            loc = yield pycos.Pycos().locate(name)
            #out = yield pycos.Pycos().peer(loc, stream_send=True)
            follower = yield pycos.Task.locate(name + SYSTEM, location=loc, timeout=TIMEOUT * 5)

            if follower != None:
                remoteDevicesSYST[name] = follower
            else:
                print("could not locate " + name + SYSTEM)

        elif msg == GOODBYE or msg == GOODBYE_MASTER:
            # remote device is saying goodbye
            del remoteDevicesSYST[name]


        elif msg in remoteDevicesSYST.keys():
            lostNode = msg
            # if a remote device advert another remote device names, we must check that it is still alive
            lostFollower = yield pycos.Task.locate(lostNode + SYSTEM, timeout=TIMEOUT)
            if lostFollower == None:
                del remoteDevicesSYST[lostNode]

        for follower in remoteDevicesSYST.values():
            follower.send(listToString()) ################################################ to be adapted

        if msg == GOODBYE_MASTER and len(remoteDevicesSYST) > 0:
            # remote device owning master is leaving, a new one must be chosen
            v = list(remoteDevicesSYST.values())
            v[0].send(ASK_MASTER)
            alive=False


if __name__ == '__main__':
    if len(sys.argv>1):
        networkName=sys.argv[1]
        if len(sys.argv>2):
            names=sys.argv[2:]
        else:
            names=[]
        masterTask(networkName,names)
    else:
        print("problem with master process, not enough args")





