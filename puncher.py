
from enum import Enum
import protocol
import ctypes as ct
import logging
import socket
import threading
from queue import Queue
from threading import Barrier
from collections import defaultdict

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
        logging.debug("Initialize PuncherServer at tcp_port=%d" % addr[1])
        protocol.ThreadedTCPServer.__init__(self, addr, PuncherHandler, PuncherPacket)
        self.conn_ids = []
        self.conn_queue_lookup = {}
        self.conn_ids_rlookup = {}
    def serve_forever(self):
        logging.debug("Starting PuncherServer.")
        protocol.ThreadedTCPServer.serve_forever(self)
    def shutdown(self):
        logging.debug("Stopping PuncherServer.")
        protocol.ThreadedTCPServer.shutdown(self)
    def next_conn_id(self):
        return len(self.conn_ids) + 1
    def nextadd_conn_id(self, node1, node2):
        conn_id = self.next_conn_id()
        logging.debug("Pairing %d-->%d, conn_id=%d" % (node1, node2, conn_id))
        conn = (node1, node2)
        self.conn_ids.append(conn)
        self.conn_ids_rlookup[conn] = conn_id
        return conn_id

class PuncherConnServer(protocol.UDPServer):
    def __init__(self, pub_ip=PUB_IP, addr=('', PORT)):
        logging.debug("Initialize PuncherConnServer at udp_port=%d" % addr[1])
        protocol.UDPServer.__init__(self, addr, PuncherConnHandler, PuncherPacket)
        self.pool_queue = {}
    def serve_forever(self):
        logging.debug("Starting PuncherConnServer.")
        protocol.ThreadedTCPServer.serve_forever(self)
    def shutdown(self):
        logging.debug("Stopping PuncherConnServer.")
        protocol.ThreadedTCPServer.shutdown(self)
                
class PuncherConnHandler(protocol.UDPHandler):
    def handle(self):
        pool_q = self.server.pool_queue
        r = self.recv()
        logging.debug("Request from %s: conn_id=%d" % ("%s:%d"%self.client_address, r.id))
        if r.id in pool_q:
            logging.debug("Both clients are here with conn_id=%d" % r.id)
            r.set_addr(pool_q[r.id])
            self.send_back(r)
            r.set_addr(self.client_address)
            self.send(r, pool_q[r.id])
        else:
            logging.debug("The other client has yet to arrive with conn_id=%d" % r.id)
            pool_q[r.id] = self.client_address

    
class PuncherHandler(protocol.Handler):
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
    def handle(self):
        q_lookup = self.server.conn_queue_lookup
        conn_ids_rl = self.server.conn_ids_rlookup
        while True:
            r = self.recv()
            action = r.get_action()
            if action == PuncherCode.BYE:
                logging.debug("Client says bye, we say bye back and quit!")
                q_lookup[self.id].put(None)
                self.send(r)
                break
            elif action == PuncherCode.JOIN:
                logging.debug("Client[id=%s] wants to join the network." % 
                    r.id)
                # check if he had joined before
                if r.id in q_lookup:
                    logging.fatal("Client[id=%s] already exists, STUB:REJOIN")
                    r.id = 0
                    self.send(r)
                    continue
                # new node, handle join and init the queue
                self.id = r.id
                q_lookup[r.id] = Queue()
                self.send(r)
            elif action == PuncherCode.CONNECT:
                logging.debug("Client[%s] wants to Client[%d]." % 
                    (self.id, r.id))
                target_id = r.id
                if target_id == self.id:
                    logging.fatal("Why are you[id=%s] connecting to yourself?" % target_id)
                    r.id = 0
                    self.send(r)
                    continue
                conn = (self.id, r.id)
                if conn in conn_ids_rl:
                    logging.fatal("Why are you[id=%s] wasting connection, the node can be reached at conn_id=%s!" % (self.id, conn_ids_rl[conn]))
                    r.id = 0
                    self.send(r)
                    continue
                if not target_id in q_lookup or not self.id in q_lookup:
                    if not target_id in q_lookup:
                        logging.fatal("Target Client[id=%s] does not exist!")
                    if not self.id in q_lookup:
                        logging.fatal("My Client[id=%s] does not exist, did you forget to join the network?")
                    r.id = 0
                    self.send(r)
                    continue
                r.id = self.server.nextadd_conn_id(self.id, r.id)
                # inform target to start UDP connection
                q_lookup[target_id].put(r)
                # we tell the remote client to setup the UDP
                self.send(r)
            elif action == PuncherCode.LISTEN:
                # Create the queue to listen to, any one who want to initate 
                # a connection with me will place it on the queue
                q = q_lookup[r.id]
                my_id = r.id
                # Server becomes the sender
                logging.debug("Server waiting for connections to: %d" % my_id)
                while True:
                    # Note, item is not mutable
                    item = q.get()
                    if item == None:
                        break
                    logging.debug("Send connection request conn_id=%d to id=%d" % (item.id, my_id))
                    self.send(item)
                # get from Q and push connection request
                r.set_action(PuncherCode.BYE)
                self.send(r)
                logging.debug("Server closed listener on %d" % r.id)
                del q_lookup[r.id]
                break
            else:
                logging.debug("STUB, Unknown packet: %s" % r)
            # just send back the same data, but upper-cased
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)

# Client will serve forever. This is a special case where client is a server as
# well.
class PuncherClient(protocol.TCPClient):
    def __init__(self, _id, EndpointPacket, server_addr=(PUB_IP, PORT)):
        logging.debug("Starting PuncherClient id=%d", _id)
        protocol.TCPClient.__init__(self, server_addr, PuncherPacket)
        self.id  = _id
        self.EndpointPacket = EndpointPacket
        self.my_addr = self.socket.getsockname()
        self.cached_conns = {}
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
            self.listener_client = PuncherClient(self.id, self.EndpointPacket, self.addr)
            listener_t = threading.Thread(target=self.listener_client.listen_forever)
            listener_t.daemon = True
            listener_t.start()
        else:
            logging.fatal("Failed to join puncher network.")
    def connect_cached(self, target_id):
        if target_id in self.cached_conns:
            logging.debug("Previously connected, returning from cache.")
            return self.cached_conns[target_id]
        else:
            logging.debug("Not connected before, starting new connection.")
            client = self.connect(target_id)
            if client.is_punched:
                logging.debug("Punch successful, storing to cache")
                self.cached_conns[target_id] = client
                return client
            else:
                logging.fatal("Punch not successful. STUB: Turn?")
    def connect(self, target_id):
        p = PuncherPacket()
        p.id = target_id
        p.set_action(PuncherCode.CONNECT)
        self.send(p)
        p = self.recv()
        if p.id == 0:
            logging.fatal("Failed to connect to id=%d" % target_id)
            return None
        else:
            logging.debug("Successfully sent request to connect, connect to conn_id=%d" % p.id)
            client = PuncherConnClient(p, self.id, self.EndpointPacket, self.addr)
            return client
    def listen_forever(self):
        logging.debug("Listening for conn_id to connect to!")
        p = PuncherPacket()
        p.id = self.id
        p.set_action(PuncherCode.LISTEN)
        self.send(p)
        p = self.recv()
        while p.get_action() != PuncherCode.BYE:
            logging.debug("Recieved new punch request with conn_id=%d" % p.id)

            client = PuncherConnClient(p, self.id, self.EndpointPacket, self.addr)
            # We spawn a new thread handling the request
            if not client.is_punched:
                return
            logging.debug("Now we spawn thread to handle incoming from client.")
            client_t = threading.Thread(target=server.handle_incoming_forever)
            client_t.daemon = True
            client_t.start()
            p = self.recv()
        logging.debug("Server terminated the listen.")

class PuncherConnClient(protocol.UDPClient):
    def __init__(self, r, _id, EndpointPacket, server_addr=(PUB_IP, PORT)):
        logging.debug("Starting PuncherConnClient conn_id=%d by id=%d" % (r.id, _id))
        protocol.UDPClient.__init__(self, server_addr, PuncherPacket)
        self.send(r)
        r = self.recv()
        if r.id == 0:
            logging.fatal("Error Puncher failed to hook us up.")
        
        # Now we set the return address to the other client
        self.set_type(r.get_addr(), PuncherPacket)
        
        # Now we perform the punch
        # If successful, the message will send the id of myself, then we will 
        # be able to identify which connection this is to.
        r.id = _id
        # In theory, this is the punching message
        self.send(r)
        # This should be recieved
        self.send(r)
        self.socket.settimeout(5)
        is_punched = False
        logging.debug("Punching for 10 times!")
        for i in range(10):
            try:
                r = self.recv()
                is_punched = True
                self.target_id = r.id
                logging.debug("Successful punch to id=%d at %s" % (r.id, "%s:%d"%self.addr))
                break
            except socket.timeout:
                logging.debug("Timeout, did not recieve the packet, retrying...")
        self.is_punched = is_punched
        if not is_punched:
            logging.fatal("Failed to punch, stop trying...")
        self.set_type(self.addr, EndpointPacket)
    def handle_incoming_forever(self):
        while True:
            try:
                # forever handle incoming requests and push the requests to queue
                p = self.recv()
                logging.debug("Endpoint incoming: %s" % str(p))
                self.send(self.incoming_endpoint(p))
                logging.debug("Endpoint outgoing: %s" % str(p))
            except socket.timeout:
                logging.fatal("Packet dropped.")
    def incoming_endpoint(self, p):
        logging.fatal("Fake endpoint, STUB, echo packets.")
        return p

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
