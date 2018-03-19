__author__ = 'mbrebion'

from libraries.i2clcda import lcd_init,lcd_string,LCD_LINE_1,LCD_LINE_2,LCD_LINE_3,LCD_LINE_4
from libraries.RotaryEncoder import RotaryEncoder
from time import sleep

import socket
import threading


class ClientThread(threading.Thread):
    def __init__(self, ip, port, clientsocket,os):
        threading.Thread.__init__(self)
        self.ip = ip
        self.os=os
        self.port = port
        self.clientsocket = clientsocket
        self.daemon=True
        self.alive=True

    def send(self,text):
        self.clientsocket.sendall(text+'\n')

    def run(self):
        self.clientsocket.settimeout(0.3)
        countFail=0
        while self.alive :
            msg=False
            try :
                r = self.clientsocket.recv(2048).decode()
                msg=r.encode("ascii").split(",")

                # in some cases, a closed client can send numerous void messages
                if msg==['']:
                    countFail+=1
                    if countFail>=5:
                        self.alive=False
                    raise socket.timeout

                if msg!=False:
                    self.os.takeAction(msg[0],int(msg[1]))
                sleep(0.02)
            except socket.timeout:
                pass
            except ValueError:
                print "too much messages received. please slow down"


        print "client as stopped"

class serverThread(threading.Thread):
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

    def sendToAll(self,text):
        # send msg to all client connected
        self.checkAliveClients()

        for client in self.clients:
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
                newthread.start()

            except:
                pass
        self.soc.close()
        print "server as stopped"


MSG_WIFI="wifi"
MSG_VOL="vol"
MSG_MENU="menu"
MSG_SELECT="select"
MSG_BACK="prev"
MSG_SHUTDOWN="sd"
MSG_BUTTON="button"

class Io(object):
    """
    class dealing with IOs
    """

    def __init__(self,os):
        # setup encoders
        self.volumeCtl=RotaryEncoder(19,23,21,"Volume")
        self.menuCtl=RotaryEncoder(11,15,13,"Menu")
        self.os=os # link to parent
        # init screen

        try :
            lcd_init()
        except IOError:
            print "no lcd screen connected"

        # TCP comm
        self.tcpServer=serverThread(os)


    def communicateTCP(self):
        pass


    def startIO(self):
        """
        main loop of os
        :return:
        """
        self.goOn=True
        while self.goOn:

            # change volume
            dec=self.volumeCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_VOL,dec)

            # change menu
            dec=self.menuCtl.getDec()
            if dec!=0 :
                self.os.takeAction(MSG_MENU,-dec) # special trick because rotary encoder for menu is mounted the wrong side on hifi_salon

            # back button status
            if self.volumeCtl.getSwitch():
                self.os.takeAction(MSG_BACK,0)

            # select button status
            if self.menuCtl.getSwitch():
                self.os.takeAction(MSG_SELECT,0)

            # exit ?
            self.os.checkStopAsked()

            self.volumeCtl.updateCurrent()
            self.menuCtl.updateCurrent()

            sleep(0.25)

        # close tcp server
        print "closing tcp server"
        self.tcpServer.shutDown()




    def writeText(self,text,line):

        # remote displays (if connected)
        self.tcpServer.sendToAll(str(line)+";;"+text)

        # LCD screen if connected
        try :
            if line==1:
                oline=LCD_LINE_1
                lcd_string(text,oline)
            if line==2:
                oline=LCD_LINE_2
                lcd_string(text,oline)
            if line==3:
                oline=LCD_LINE_3
                lcd_string(text,oline)
            if line==4:
                oline=LCD_LINE_4
                lcd_string(text,oline)

        except IOError:
            print "screen disconnected"

