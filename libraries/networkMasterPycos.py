import socket,sys
import pycos
from time import sleep
import pycos.netpycos


# usefull constants

TIMEOUT=1.5
STATUS_MASTER="master"
STATUS_FOLLOWER="follower"

MASTER_PORT=34061

SHOW_ALL="showAll"
HELLO="hello" # message send when first connecting to master
GOODBYE="goodbye" # message send when leaving network
GOODBYE_MASTER="goodbye_master" # message send when master node leaving network
ASK_MASTER="ask_master"
NEW_MASTER="new_master"
SYSTEM= "_system"
MASTER="_master"
COMM="_comm"
ipv4_udp_multicast="239.255.10.10"



# master must advertize remotes when newly created because else , remotes won't notice it has changed

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

def listToString(remoteDevicesSYST):
        out=""
        for e in remoteDevicesSYST.keys():
            out+=e+","
        return out[0:-1]


alive=True
def masterTask(networkTag,names, task=None):
    """

    :param names: list of already known nodes (usefull when master is created after a former master failure
    :param task:
    :return:
    """
    global alive
    task.register(networkTag+MASTER)


    print("*** master task : " + networkTag+MASTER)
    remoteDevicesSYST = {}

    for name in names:
        loc = yield pycos.Pycos().locate(name,timeout=TIMEOUT*2)
        print("***!* "+str(loc)+"  "+name)

        if loc!=None:
            follower = yield pycos.Task.locate(name + SYSTEM,location=loc, timeout=TIMEOUT)
        else:
            follower=None
            print("*** master did not found "+name)

        if follower != None:
            print("*** master initiated with follower : "+name+ " at "+str(follower))
            remoteDevicesSYST[name] = follower
            follower.send(NEW_MASTER+","+str(pycos.Pycos().location))
            follower.send(listToString(remoteDevicesSYST)) ################################################ to be adapted

    while alive:
        # receive message
        msgName = yield task.receive(TIMEOUT)
        if msgName == None:
            continue
        try:
            name, msg = msgName.split(",")
        except:
            print("*** strange mess received ", msgName)

        # messages kind : HELLO tag , GOODBYE tag or existing name

        if msg == HELLO:
            # new (or not) remote device is saying hello
            print("*** received hello from ", name)

            loc = yield pycos.Pycos().locate(name)
            follower = yield pycos.Task.locate(name + SYSTEM, location=loc, timeout=TIMEOUT * 5)

            if follower != None:
                remoteDevicesSYST[name] = follower
            else:
                print("*** could not locate " + name + SYSTEM)

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
            follower.send(listToString(remoteDevicesSYST)) ################################################ to be adapted

        if msg == GOODBYE_MASTER:
            # remote device owning master is leaving, a new one must be chosen
            print("*** master asked to dye")
            if len(remoteDevicesSYST) > 0:
                list(remoteDevicesSYST.values())[0].send(ASK_MASTER)

            alive=False



if __name__ == '__main__':
    if len(sys.argv)>1:

        networkName=sys.argv[1]
        if len(sys.argv)>2:
            names=sys.argv[2:]
        else:
            names=[]

        print("*** names received" + str(names))
        pycos.Pycos(node=get_ip(), name=networkName,tcp_port=MASTER_PORT,ipv4_udp_multicast=ipv4_udp_multicast)
        print("*** master location "+str(pycos.Pycos().location))
        task=pycos.Task(masterTask,networkName,names)
        while alive:
            sleep(0.1)
        print("*** master definitely dead")
        #task.unregister(networkName+MASTER)
        pycos.Pycos().terminate()
        pycos.Pycos().finish()

    else:
        print("problem with master process, not enough args")





