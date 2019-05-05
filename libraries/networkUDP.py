import threading
import sys
import asyncio
import socket
import time
import struct


MULTICAST_ADDR = "239.255.4.3"
ANNOUNCE_ALIVE_DELAY = 10 # time (in s) between annoucement, must be >=1 s)
TIMEOUT=1

udpPort=3234
tcpPortServer=4112

SEP=":,:"
TERM="/EOL"
TERMtcp=b"/EOL"

DEST_ALL="toAll"
MSG_ALIVE = "alive"
MSG_HELLO = "hello"
MSG_HRU = "howRu"
MSG_LEAVING = "bye"
MSG_USER = "user"
MSG_USER_CONFIRM = "userC"
MSG_QUIT_TCP="quitQUITquit"


#############################################################################
###################### utilities classes and functions ######################
#############################################################################

class _TCPNetwork(threading.Thread):
    """
    listening thread
    """
    def __init__(self,node=None):
        """
        this thread is launched right after being instanciated,
        """
        if node is None:
            self.nUDP = NetworkUDP()  # retrieve the sole instance of NetworkUDP
        else:
            self.nUDP=node

        self.loopCreated=False
        threading.Thread.__init__(self)
        self.printers={}

        self.start()





    def run(self):
        try:
            asyncio.run(self.main())
        except asyncio.CancelledError:
            print("asyncio loop closed")



    async def main(self):
        self.loop = asyncio.get_event_loop()
        self.loopCreated = True
        self.server =  await asyncio.start_server(self.handle_client, "", tcpPortServer,start_serving=False)
        async with self.server:
            await self.server.serve_forever()   # this appears to be a blocking call



    async def handle_client(self, reader, writer,name=False):
        request = None

        addr = writer.get_extra_info('peername')


        if name==False :
            #print(" (receiver) tcp connexion established with ", addr)
            sender = await reader.readuntil(TERMtcp)
            sender = self.decode(sender)
        else :

            #print(" (asker) tcp connexion established with ", addr)
            sender=name

        #print("its name is ", sender)
        self.printers[sender] = writer
        # connexion lost count
        count=0

        # receiving loop
        while request != MSG_QUIT_TCP and self.nUDP.alive and count<3:
            try :
                request = self.decode(await asyncio.wait_for(reader.readuntil(TERMtcp), timeout=TIMEOUT))  # is it working
                if request.isspace():
                    count+=1
                    continue
            except :
                continue

            #request = self.decode(await reader.read(255))

            #print("request |",request,"|      received from ",sender)

            try:
                self.nUDP.funcRecep(request, sender)
                count=0
            except:
                count+=1
        #print("connection stopped with ", sender)
        self.nUDP._host_has_left(sender)


    def format(self, ins):
        return (ins).encode('utf8') + TERMtcp

    def decode(self, ins):
        return ins.decode('utf8').replace(TERM,"")


    def remove_tcp_printer(self, name):
        self.printers[name].write(self.format(MSG_QUIT_TCP))
        del self.printers[name]



    async def tcpSendAS(self, name, message):
        #print("sending ", message, "    to ", name)
        self.printers[name].write(self.format(message))
        await self.printers[name].drain()

    async def add_tcp_printer(self, addr, name):
        reader, writer = await asyncio.open_connection(addr, tcpPortServer)
        self.printers[name] = writer
        asyncio.ensure_future(self.handle_client(reader, writer, name=name))
        writer.write(self.format(self.nUDP.name))
        await writer.drain()

    async def closeProperly(self):
        for key, value in self.printers.items():

            value.write(self.format(MSG_QUIT_TCP))

        self.server.close()
        await self.server.wait_closed()
        await self.loop.shutdown_asyncgens()



    ####### functions called from outside

    def add_printer_from_outside(self, addr, name):
        """
        Add tcp printer (helper method for add_tcp_printer)
        :param addr: addr of remote host
        :param name: name of remote host
        :return:
        """
        asyncio.run_coroutine_threadsafe(self.add_tcp_printer(addr, name),self.loop)

    def tcpSend_from_outside(self, name, message):
        """
        Send message (helper method for tcpSendAS)
        :param name: host's name
        :param message: message to be sent
        :return:
        """
        asyncio.run_coroutine_threadsafe(self.tcpSendAS(name,message),self.loop)

    def closeProperly_from_outside(self):

        future=asyncio.run_coroutine_threadsafe(self.closeProperly(), self.loop)
        return future.result()



#############################################################################
#######################  end of TCP section  ################################
#############################################################################



class RemoteInfo:
    """
    class used to store informations about other devices
    """

    def __init__(self, name="", address=""):
        self.name = name
        self.address = address
        self.lastSeen = time.time()

class Singleton(type):
    """
    Meta class for singleton instances.
    """
    _memo = {}

    def __call__(cls, *args, **kwargs):
        """
        kind of class cls to be instanciated
        object of class cls is obtained by using __call__ from parent class of Singleton (type)
        which is is base metaclass to use to generate objects
        :param args: args passed to cls.__init__()
        :param kwargs: kargs passed to cls.__init__()
        :return: singleton instance of cls
        """
        if cls not in Singleton._memo:
            Singleton._memo[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return Singleton._memo[cls]

    @classmethod
    def empty(_, cls):
        """
        Forget singleton instance. Usefull for being able to create a new one
        """
        Singleton._memo.pop(cls, None)

class _UDPNetwork(threading.Thread):
    """
    listening thread
    """
    def __init__(self,node=None):
        """
        this thread is launched right after being instanciated,
        """
        if node is None:
            self.nUDP = NetworkUDP()  # retrieve the sole instance of NetworkUDP
        else:
            self.nUDP=node

        threading.Thread.__init__(self)

        self.start()

    def concerned(self, dests):
        return self.nUDP.name in dests or DEST_ALL in dests

    def run(self):
        lastSent=time.time()

        # message sent two times (safer)
        self.nUDP._sendMSG(self.nUDP.name, kind=MSG_HELLO)
        time.sleep(0.002)
        self.nUDP._sendMSG(self.nUDP.name, kind=MSG_ALIVE)


        #start tcp server and wait


        # loop udp advertizing and multicast

        while self.nUDP.alive:
            # Data waits on socket buffer until we retrieve it.
            # NOTE: Normally, you would want to compare the incoming data's source address to your own, and filter it out
            #       if it came from the current machine. Everything you send gets echoed back at you if your socket is
            #       subscribed to the multicast group.

            now=time.time()
            if now-lastSent>ANNOUNCE_ALIVE_DELAY:
                self.nUDP._sendMSG(self.nUDP.name, kind=MSG_ALIVE)
                lastSent=now


            try:
                data, address = self.nUDP.my_recvsocket.recvfrom(256)  # TODO : to be improved
                data=data.decode()

                if not data.endswith(TERM):
                    print("partial message is received - we must deal with it")
                    print(data)
                    print()
                    continue
                else :
                    data=data.replace(TERM,"")

                chain = data.split(SEP)
                kind,dests,message = chain
                if not self.concerned(dests):
                    continue

                sender = "unknown"
                for remote in self.nUDP.remoteDevices.values():
                    if remote.address == address:
                        sender = remote.name
                        break

            except socket.timeout:
                continue
            except IndexError:
                print("received a message in the wrong format (index error): " + data)
                continue

            if kind == MSG_HRU:
                print("received HRU from ", sender)
                self.nUDP._sendMSG(self.nUDP.name, MSG_ALIVE)

            elif kind == MSG_HELLO:
                self._dealWithALIVE(message, address,first=True)

            elif kind == MSG_ALIVE:
                self._dealWithALIVE(message, address)

            elif kind == MSG_LEAVING:
                self._dealWithLeaving(message)

            elif kind == MSG_USER:
                # we must find the sender by checking its IP and PORT
                self._dealWithALIVE(sender, address)
                self.nUDP.funcRecep(message, sender)
            else:
                print("received : " + data + " from " + str(address))

            self._checkStillALIVE()

        self.nUDP.my_sendSocket.close()
        self.nUDP.my_recvsocket.close()


    def _checkStillALIVE(self):
        toKill = []
        tim = time.time()
        for name in self.nUDP.remoteDevices.keys():
            lastSeen = self.nUDP.remoteDevices[name].lastSeen

            if (tim - lastSeen) > ANNOUNCE_ALIVE_DELAY * 3.1:
                self.nUDP._sendMSG(self.nUDP.name,MSG_HRU,dest=name)


            if (tim - lastSeen) > ANNOUNCE_ALIVE_DELAY * 5.1:  # can miss up to 5 alive messages before warning
                toKill.append(name)

        changes = False
        for name in toKill:
            changes = True
            del self.nUDP.remoteDevices[name]
        if changes:
            self.nUDP.funcHostsUpdate(self.nUDP.remoteDevices)

    def _dealWithALIVE(self, nameOfRemote, address,first=False):
        if nameOfRemote not in self.nUDP.remoteDevices or first:
            self.nUDP.remoteDevices[nameOfRemote] = RemoteInfo(name=nameOfRemote, address=address)

            self.nUDP.funcHostsUpdate(self.nUDP.remoteDevices) # advert the user with the function he has provided (default func just print remotes names)

            # we then announce to him if its not us :
            if nameOfRemote != self.nUDP.name and first:
                self.nUDP._sendMSG(self.nUDP.name,MSG_ALIVE,dest=nameOfRemote)
                time.sleep(0.001) # resend the message might be safer
                self.nUDP._sendMSG(self.nUDP.name, MSG_ALIVE, dest=nameOfRemote)

            if nameOfRemote >self.nUDP.name :
                # because of the > opp, there is only one tcp conection between two host

                self.nUDP.tcp.add_printer_from_outside(address[0],nameOfRemote)

        else:
            self.nUDP.remoteDevices[nameOfRemote].lastSeen = time.time()

    def _dealWithLeaving(self, nameOfRemote):
        if nameOfRemote in self.nUDP.remoteDevices.keys():
            del self.nUDP.remoteDevices[nameOfRemote]
            self.nUDP.funcHostsUpdate(self.nUDP.remoteDevices)


def _defaultRecep(msg, source):
    """
    default function used when a user message (not a one used for maintaining the network) is received

    :param msg: message reiceved (str)
    :param source: author of the message (str:name)
    :return: nothing
    """
    print("** ** ** **received  : " + msg + "   from " + source)


def _defaultHostUpdate(hosts):
    """
    default function used when there is a change in the known's hosts (a host has leaved or reached the network)
    :param hosts: dict in which keys are the name of the remote devices and the values are of class _remoteInfo
    :return: nothing
    """
    print("known hosts " + str(hosts.keys()))


#############################################################################
########################### Main class of package ###########################
#############################################################################

class NetworkUDP(metaclass=Singleton):
    """
    Main class of the project used to deal with network communications.
    """

    def __init__(self, name=None, multicast_ip=MULTICAST_ADDR, port=udpPort, fr=_defaultRecep, fhu=_defaultHostUpdate):

        """
        This class can only be instanciated once, any attempts to re-instanciate it will provide the same object (singleton patern)
        However, this class is not thread safe, do not use it from different threads in the same time.

        :param multicast_ip: ip used for multicast from 239.0.0.0 to 239.255.255.252, default is MULTICAST_ADDR value
        (these addresses are Administratively scoped and intented to be used on local networks only)
        :param port: port used to receive message (port+1 is used to send them)
        :param name: name of the node (if not provided, tha name of the host is used instead
        :param fr: function called when a user message is received, default function,
        if no other is provided, simply print the message and its author's name
        :param fhu: function called when a new host join the network of if a former host leave it,
        default function print the list of remaining known hosts
        """

        self.multicast_ip = multicast_ip
        self.port = port
        self.funcRecep = fr
        self.funcHostsUpdate = fhu

        global ANNOUNCE_ALIVE_DELAY
        if ANNOUNCE_ALIVE_DELAY<1:
            print("ANNOUNCE_ALIVE_DELAY is too small, a value of 30 s is used instead")
            ANNOUNCE_ALIVE_DELAY=30

        if name is not None:
            self.name = name
        else:
            self.name = socket.gethostname()

        self.alive = True
        self.remoteDevices = {}

        self.my_sendSocket = self._create_socket(multicast_ip, port + 1)
        self.my_recvsocket = self._create_socket(multicast_ip, port)

        # these threads are started right after being created
        self.tcp = _TCPNetwork(self)
        while(not self.tcp.loopCreated):
            time.sleep(0.001)
        self.llt = _UDPNetwork(self)


    ####### internal methods #######
    def _host_has_left(self,name):
        if name in self.remoteDevices:
            del self.remoteDevices[name]
            self.funcHostsUpdate(self.remoteDevices)

    def _create_socket(self, multicast_ip, port):
        """
        Creates a socket, sets the necessary options on it, then binds it. The socket is then returned for use.
        """
        local_ip = self.get_local_ip()

        # create a UDP socket
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.settimeout(TIMEOUT)  # wait no more than half second

        # allow reuse of addresses
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # set multicast interface to local_ip
        my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))

        # Set multicast time-to-live to 2...should keep our multicast packets from escaping the local network
        my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        # Construct a membership request...tells router what multicast group we want to subscribe to
        membership_request = socket.inet_aton(multicast_ip) + socket.inet_aton(local_ip)

        # Send add membership request to socket
        # See http://www.tldp.org/HOWTO/Multicast-HOWTO-6.html for explanation of sockopts
        my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_request)

        # Bind the socket to an interface.
        # If you bind to a specific interface on osx or linux, no multicast data will arrive.
        # If you try to bind to all interfaces on Windows, no multicast data will arrive.
        # Hence the following.
        if sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            my_socket.bind(('0.0.0.0', port))
        else:
            my_socket.bind((local_ip, port))

        return my_socket

    def _get_bound_multicast_interface(self, my_socket):
        """
        Returns the IP address (probably your local IP) that the socket is bound to for multicast.
        Note that this may not be the same address you bound to manually if you specified 0.0.0.0.
        This isn't used here, just a useful utility method.
        """
        response = my_socket.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF)
        socket.inet_ntoa(struct.pack('i', response))

    def _drop_multicast_membership(self, my_socket, multicast_ip):
        """
        Drops membership to the specified multicast group without closing the socket.
        Note that this happens automatically (done by the kernel) if the socket is closed.
        """

        local_ip = self.get_local_ip()

        # Must reconstruct the same request used when adding the membership initially
        membership_request = socket.inet_aton(multicast_ip) + socket.inet_aton(local_ip)

        # Leave group
        my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, membership_request)

    def _sendMSG(self, msg, kind, dest=DEST_ALL):
        """
        send message to all host, only those targeted in dest will react
        :param msg: message to send
        :param kind: kind of message (MSG_ALIVE or MSG_LEAVING or MSG_USER)
        :param dest: name of target or list of names of targets or DEST_ALL (everyone)
        :return: True if all dest are known host, else False, msg is only send to known hosts
        """
        allFound = True

        if not self.alive:
            return

        if kind not in [MSG_ALIVE, MSG_LEAVING, MSG_USER,MSG_HELLO,MSG_HRU,MSG_USER_CONFIRM]:
            print("kind " + kind + " not allowed for sending messages")
            return False

        destStr = "["
        if not isinstance(dest, list):
            dest = [dest]

        for name in dest:
            if name not in self.remoteDevices.keys() and name != DEST_ALL:
                allFound = False
            else:
                destStr += name + ","
        destStr = destStr[:-1] + "]"  # removing last comma  and adding final bracket

        message = kind + SEP + destStr + SEP + msg + TERM  # this is the only format accepted for messages
        self.my_sendSocket.sendto(message.encode(), (self.multicast_ip, self.port))
        return allFound


    ####### methods the user may use #######
    def get_local_ip(self):
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

    @classmethod
    def instance(cls, *args, **kwargs):
        """Returns (singleton) instance of Pycos.
        """
        return cls(*args, **kwargs)

    def sendMSG(self,msg,dest=DEST_ALL,confirm=False):
        """
        function used to send messages to other remotes
        :param msg: the message to be sent
        :param dest: name (or list of names) of remotes devices which are concerned by this message
        :param confirm: if set to True, a confirmation is waited to ensure this message has been correctly received. Do not work with DEST_ALL, This function is then blocking
        :return: true if all receivers are known host, else false
        """

        if not dest == DEST_ALL:
            # message not targeting all dest are send via TCP (and thus, without multicast)
            if not isinstance(dest, list):
                dest = [dest]
            for d in dest:
                self.tcp.tcpSend_from_outside(d, msg)
        else :
            return self._sendMSG(msg,MSG_USER,dest)


    def leaveNetwork(self):
        """
        announce the network that we are leaving
        everything is then cleared properly
        :return: nothing
        """


        self._sendMSG(self.name, MSG_LEAVING, DEST_ALL)
        self._drop_multicast_membership(self.my_sendSocket, self.multicast_ip)
        self._drop_multicast_membership(self.my_recvsocket, self.multicast_ip)
        self.alive = False
        self.tcp.closeProperly_from_outside()



        Singleton.empty(NetworkUDP)


if __name__ == '__main__':
    nUDP = NetworkUDP()
    print(" test of udp network")
    goOn = True
    while goOn:
        msg = input()
        if msg == "quit":
            goOn = False
            nUDP.leaveNetwork()
            continue
        nUDP.sendMSG(msg)
