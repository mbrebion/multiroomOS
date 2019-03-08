__author__ = 'mbrebion'


import socket
from time import sleep
import threading
from config import host,hortPort,name
from libraries.constants import MSG_PROPAGATE_ORDER,MSG_ORDER

from libraries.constants import CLIENT_DEVICE,CLIENT_REMOTE,CLIENT_MAIN


def connectToHost():
    """
    function used by simple hifi devices to connect to host (main hifi device)
    """
    socket.setdefaulttimeout(0.5)
    try :
        addr=socket.gethostbyname(host+".local")
    except socket.gaierror :
        return False
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.settimeout(0.5)
    try :
        skt.connect((addr, hortPort))
        skt.sendall(CLIENT_DEVICE.encode()) # send kind of client to host
    except socket.error :
        return False

    return skt



class ClientThread(threading.Thread):
    """
    This class deals a connection between a client and a host.
    It is used to deals requests coming from outer client
    """
    def __init__(self, ip, port, clientsocket,os):
        threading.Thread.__init__(self)
        self.ip = ip
        self.os=os
        self.port = port
        self.clientsocket = clientsocket
        self.daemon=True
        self.alive=True

        self.kind = self.clientsocket.recv(64).decode("utf-8") # kind of client : can be device or remoteControl or mainPlayer
        if self.kind==CLIENT_DEVICE:
            self.clientsocket.sendall(CLIENT_MAIN.encode())

        self.start()


    def send(self,text):
        self.clientsocket.sendall((text+'\n').encode())

    def run(self):
        self.clientsocket.settimeout(0.3)
        countFail=0
        while self.alive :

            try :
                r = self.clientsocket.recv(64).decode("utf-8")
                msg=r.split(",")
                # in some cases, a closed client can send numerous void messages
                if msg==['']:
                    countFail+=1
                    if countFail>=5:
                        self.alive=False
                        print("client disconnected : ", self.ip)
                    raise socket.timeout

                if msg != False:
                    if msg[0]==MSG_PROPAGATE_ORDER:
                        # in this case, the order is treated and propagated to other devices
                        self.os.takeAction(msg[1],int(msg[2]),msg[3])
                        self.os.io.tcpServer.propagateMessage(msg[1]+","+msg[2]+","+msg[3],self)
                    else:
                        self.os.takeAction(msg[0],int(msg[1]),msg[2])
                sleep(0.02)


            except socket.timeout:
                pass
            except ValueError:
                print("too much messages received. please slow down : ")
            except :
                print("unknown error with tcp")
                print(msg)


        if self.kind==CLIENT_MAIN:
            self.os.connectionLost()
        #print "client has stopped"





###############################################################################################
######################################### server side #########################################
###############################################################################################



class serverThread(threading.Thread):
    """
    This class deals with the server awaiting for outer client connections.
    Once a client connect, a new client thread is allocated and will deal with it until end of connection.
    """
    def __init__(self, os):
        # init socket comm
        threading.Thread.__init__(self)
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.bind(('', 15555))
        self.clients=[]
        self.alive=True
        self.os = os
        self.daemon=True
        self.start()

    def sendToAllDevices(self,text):
        # send msg to all client connected
        self.checkAliveClients()

        for client in self.clients:
            if client.kind==CLIENT_DEVICE:
                try:
                    client.send(text)
                except :
                    print("error in send to client device (_sendMSG)")
                    client.alive=False


    def propagateMessage(self,text,source):
        # send msg to all devices included this one, except to the one who sent the message
        self.checkAliveClients()

        for client in self.clients:
            if client.kind == CLIENT_DEVICE and client != source:
                try:
                    client.send(text)
                except :
                    print("error in send to client device (propagate)")
                    client.alive=False




    def sendToAllRemotes(self,text):
        # send msg to all client connected
        self.checkAliveClients()

        for client in self.clients:
            if client.kind == CLIENT_REMOTE:
                #try :
                client.send(text)
                #except :
                #    print("error in send to client remotes")
                #    client.alive=False

    def checkAliveClients(self):
        for client in self.clients:
            if client.alive==False:
                self.clients.remove(client)


    def shutDown(self):
        self.alive=False
        for client in self.clients:
            client.alive=False


    def run(self):
        self.soc.listen(8)
        self.soc.settimeout(0.3)
        while self.alive:
            try :
                (clientsocket, (ip, port)) = self.soc.accept()

                newthread = ClientThread(ip, port, clientsocket,self.os)
                self.clients.append(newthread)
                print("client connected : ", ip)

            except:
                pass
        self.soc.close()
        print("server as stopped")
