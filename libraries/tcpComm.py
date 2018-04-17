__author__ = 'mbrebion'


import socket
from time import sleep
import threading
from config import host,hortPort
from libraries.constants import CLIENT_DEVICE,CLIENT_REMOTE,CLIENT_MAIN


def connectToHost():

    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.settimeout(0.4)
    try :
        skt.connect((host, hortPort))
        skt.sendall(CLIENT_DEVICE) # send kind of client to host
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

        self.kind = self.clientsocket.recv(512).decode().encode("ascii") # kind of client : can be device or remoteControl or mainPlayer
        #print "kind of client : " , self.kind
        if self.kind==CLIENT_DEVICE:
            self.clientsocket.sendall(CLIENT_MAIN)

        self.start()

    def send(self,text):
        self.clientsocket.sendall(text+'\n')

    def run(self):
        self.clientsocket.settimeout(0.3)
        countFail=0
        while self.alive :

            try :
                r = self.clientsocket.recv(512).decode()
                msg=r.encode("ascii").split(",")

                # in some cases, a closed client can send numerous void messages
                if msg==['']:
                    countFail+=1
                    if countFail>=5:
                        self.alive=False
                        print "client disconnected : ", self.ip
                    raise socket.timeout

                if msg!=False:
                    self.os.takeAction(msg[0],int(msg[1]))
                sleep(0.02)


            except socket.timeout:
                pass
            except ValueError:
                print "too much messages received. please slow down"

        if self.kind==CLIENT_MAIN:
            self.os.connectionLost()
        #print "client has stopped"


class serverThread(threading.Thread):
    """
    This class deals with the server awaiting for outer client connections.
    One a client connect, a new client thread is allocated and will deal with it until end of connection.
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
                client.send(text)

    def sendToAllRemotes(self,text):
        # send msg to all client connected
        self.checkAliveClients()

        for client in self.clients:
            if client.kind==CLIENT_REMOTE:
                client.send(text)

    def checkAliveClients(self):
        for client in self.clients:
            if client.alive==False:
                self.clients.remove(client)


    def shutDown(self):
        self.alive=False
        for client in self.clients:
            client.alive=False


    def run(self):
        self.soc.listen(5)
        self.soc.settimeout(0.2)
        while self.alive:
            try :
                (clientsocket, (ip, port)) = self.soc.accept()

                newthread = ClientThread(ip, port, clientsocket,self.os)
                self.clients.append(newthread)
                print "client connected : ", ip

            except:
                pass
        self.soc.close()
        print "server as stopped"
