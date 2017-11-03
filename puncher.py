
from enum import Enum
import protocol
import ctypes as ct
import logging
import socket
import threading
from queue import Queue

class PuncherCode(Enum):
    BYE = 0
    JOIN = 1
    CONNECT = 2
    LISTEN = 3

PORT = 50818
PUB_IP = "127.0.0.1"

class PuncherPacket(ct.Structure):
    _fields_ = [("ip", ct.c_ubyte * 4),
                ("port", ct.c_ushort),
                ("action", ct.c_ushort),
                ("id", ct.c_int)]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return PuncherCode(self.action)
    def set_addr(self, addr):
        self.ip = protocol.pack_ip(addr[0])
        self.port = addr[1]
    def get_addr(self):
        return (protocol.unpack_ip(self.ip), self.port)
    def __str__(self):
        return "%s:%s:%s" % (str(self.get_addr()),
            str(PuncherCode(self.action)),
            str(self.id))
    
class PuncherServer(protocol.ThreadedTCPServer):
    def __init__(self, pub_ip=PUB_IP, addr=('', PORT)):
        logging.debug("Starting PuncherServer at port=%d" % addr[1])
        protocol.ThreadedTCPServer.__init__(self, addr, PuncherHandler, PuncherPacket)
        self.conn_ids = []
        self.conn_queues = {}
    def shutdown(self):
        logging.debug("Stopping PuncherServer.")
        protocol.ThreadedTCPServer.shutdown(self)
    def next_conn_id(self):
        return len(self.conn_ids) + 1
    def nextadd_conn_id(self, node1, node2):
        conn_id = self.next_conn_id()
        logging.debug("Pairing %d<->%d, conn_id=%d" % (node1, node2, conn_id))
        self.conn_ids.append((node1, node2))
        return conn_id

class PuncherConnectionServer(protocol.ThreadedUDPServer):
    def __init__(self, pub_ip=PUB_IP, addr=('', PORT)):
        logging.debug("Starting PuncherDataServer at port=%d" % addr[1])
        protocol.ThreadedUDPServer.__init__(self, addr, PuncherDataHandler, PuncherPacket)

class PuncherHandler(protocol.Handler):
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
    def handle(self):
        while True:
            r = self.recv()
            action = r.get_action()
            if action == PuncherCode.BYE:
                logging.debug("Client says bye, we say bye back and quit!")
                self.server.conn_queues[self.id].put(None)
                self.send(r)
                break
            elif action == PuncherCode.JOIN:
                logging.debug("Client[id=%s] wants to join the network." % 
                    r.id)
                r.set_addr(self.client_address)
                self.id = r.id
                self.send(r)
            elif action == PuncherCode.CONNECT:
                logging.debug("Client[%s] wants to Client[%d]." % 
                    (self.id, r.id))
                target_id = r.id
                r.id = self.server.nextadd_conn_id(self.id, r.id)
                # inform both to start UDP connection
                self.server.conn_queues[target_id].put(r)
                self.server.conn_queues[self.id].put(r)
                self.send(r)
            elif action == PuncherCode.LISTEN:
                # Create the queue to listen to, any one who want to initate 
                # a connection with me will place it on the queue
                q = Queue()
                self.server.conn_queues[r.id] = q
                my_id = r.id
                # Server becomes the sender
                logging.debug("Server waiting for conn_id to send to: %d" % my_id)
                while True:
                    # Note, item is not mutable
                    item = q.get()
                    if item == None:
                        break
                    print(item)
                    logging.debug("Send connection request conn_id=%d to id=%d" % (item.id, my_id))
                    self.send(item)
                # get from Q and push connection request
                r.set_action(PuncherCode.BYE)
                self.send(r)
                logging.debug("Server closed listener on %d" % r.id)
                break
            else:
                logging.debug("STUB, Unknown packet: %s" % r)
            # just send back the same data, but upper-cased
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)

# Client will serve forever. This is a special case where client is a server as
# well.
class PuncherClient(protocol.TCPClient):
    def __init__(self, _id):
        logging.debug("Starting PuncherClient id=%d", _id)
        protocol.TCPClient.__init__(self, (PUB_IP, PORT), PuncherPacket)
        self.id  = _id
        self.my_addr = self.socket.getsockname()
    def bye(self):
        logging.debug("Initiate shutdown.")
        p = PuncherPacket()
        p.set_action(PuncherCode.BYE)
        self.send(p)
        p = self.recv()
        if PuncherCode(p.action) == PuncherCode.BYE:
            self.close()
            logging.debug("Shutdown successful.")
    def join(self):
        # Tell the server my unique id
        p = PuncherPacket()
        p.set_action(PuncherCode.JOIN)
        p.id = self.id
        p.set_addr(self.my_addr)
        self.send(p)
        p = self.recv()
        if p.id != 0:
            logging.debug("Joined puncher network successfully, pub_ip=%s:%d" % p.get_addr())
            self.listener_client = PuncherClient(self.id)
            listener_t = threading.Thread(target=self.listener_client.listen_forever)
            listener_t.daemon = True
            listener_t.start()
        else:
            logging.fatal("Failed to join puncher network.")
    def connect(self, target_id):
        p = PuncherPacket()
        p.id = target_id
        p.set_action(PuncherCode.CONNECT)
        self.send(p)
        p = self.recv()
    def listen_forever(self):
        logging.debug("Listening for conn_id to connect to!")
        p = PuncherPacket()
        p.id = self.id
        p.set_action(PuncherCode.LISTEN)
        self.send(p)
        p = self.recv()
        while p.get_action() != PuncherCode.BYE:
            # Do something
            logging.debug("Recieved new request, connecting to server to punch with conn_id=%d" % p.id)
            logging.debug(p)
            p = self.recv()
        logging.debug("Server terminated the listen.")

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
