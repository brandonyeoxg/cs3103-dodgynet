from enum import Enum
import protocol
import ctypes as ct
import logging

class TrackerCode(Enum):
    BYE = 0
    JOIN = 1
    ANNOUNCE = 2
    WANT = 3

PORT = 60760
PUB_IP = "127.0.0.1"

class TrackerPacket(ct.Structure):
    _fields_ = [("action", ct.c_uint),
                ("peer_id", ct.c_uint)] # Represents in [Announce Request: Num Chunk Have] [Want Request: Num Chunk Want] [Want Response: Peer A peer id]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return TrackerCode(self.action)
    def set_addr(self, addr):
        self.ip = protocol.pack_ip(addr[0])
        self.port = addr[1]
    def get_addr(self):
        return (protocol.unpack_ip(self.ip), self.port)
    def __str__(self):
        return "%s:%s" % (str(TrackerCode(self.action)),
            str(self.peer_id))

class TrackerServer(protocol.ThreadedTCPServer):
    def __init__(self, pub_ip=PUB_IP, addr=('', PORT)):
        logging.debug("Initialize TrackerServer at tcp_port=%d" % addr[1])
        protocol.ThreadedTCPServer.__init__(self, addr, TrackerHandler, TrackerPacket)
        self.peer_lookup = {}
        self.peer_list_ctr = 0

class TrackerHandler(protocol.Handler):
    class Peer(object):
        def __init__(self, peer_id, addr):
            self.peer_id = peer_id
            self.addr = addr
        def __str__(self):
            return "%s-%s" % (self.peer_id, "%s:%d"%self.addr)
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
        # STUB
        self.peer_lookup = self.server.peer_lookup
    def handle(self):
        # data here
        while True:
            r = self.recv()
            print(r)
            action = r.get_action()
            if action == TrackerCode.BYE:
                logging.debug("Client says bye, we say bye back and quit!")
                self.send(r)
                break
            elif action == TrackerCode.JOIN:
                logging.debug("Client wants to join the network, generate it a new id.")
                peer_id = self.generatePeerId()
                logging.debug("Peer will be assigned id=%d" % peer_id)
                r.peer_id = peer_id
                self.send(r)
                self.peer_id = peer_id
                self.add_peer(self.peer_id)
                self.debug_print_active_peers()
            elif action == TrackerCode.ANNOUNCE:
                logging.debug("Client announces that it has a particular chunk.")
            elif action == TrackerCode.WANT:
                logging.debug("Client says bye, we say bye back and quit!")
            else:
                logging.fatal("Unknown format, %s" % r)
        self.delete_peer_from_list(self.peer_id)
        self.debug_print_active_peers()
    def debug_print_active_peers(self):
        logging.debug("Active peers: [%s]" % ', '.join([ str(p) for p in self.peer_lookup.values()]) )
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)
    def delete_peer_from_list(self, peer_id):
        print("Delete peer from list!")
        del self.peer_lookup[peer_id]
    def add_peer(self, peer_id):
        # we no longer need to track port so can remove
        self.peer_lookup[peer_id] = TrackerHandler.Peer(peer_id, self.client_address)
        
    def update_peer_chunk(self, peer_id, chunk_have):
        for peer in self.peer_lookup:
            if peer['peer_id'] == peer_id:
                peer['chunk_have'].append(chunk_have)
                print("========= Peer " + str(peer['peer_id']) + " Chunks =========")
                print(peer['chunk_have'])
    def get_peers_by_chunk_num(self, chunk_want):
        peer_with_chunk = []
        for peer in self.peer_lookup:
            if chunk_want in peer['chunk_have']:
                # remove port, replace it with peer_id of the client
                peer_with_chunk.append({'ip_addr': peer['ip_addr'], 'port': peer['port']})
        return peer_with_chunk
    def generatePeerId(self):
        self.server.peer_list_ctr += 1
        return self.server.peer_list_ctr
        
class TrackerClient(protocol.TCPClient):
    def __init__(self, server_addr=(PUB_IP, PORT)):
        logging.debug("Starting TrackerClient.")
        protocol.TCPClient.__init__(self, server_addr, TrackerPacket)
    def join(self):
        # can form a tracker packet here and send it into the send method
        join_request_pkt = TrackerPacket()
        join_request_pkt.set_action(TrackerCode.JOIN)
        self.send(join_request_pkt)
        join_response_pkt = self.recv()
        if join_response_pkt.peer_id != 0:
            logging.debug("Joined tracker network successfully, with id=%d" % join_response_pkt.peer_id)
        else:
            logging.fatal("Failed to join tracker network.")
        return join_response_pkt.peer_id
    def bye(self):    
        logging.debug("Initiate shutdown.")
        bye_request_pkt = TrackerPacket()
        bye_request_pkt.set_action(TrackerCode.BYE)
        self.send(bye_request_pkt)
        bye_response_pkt = self.recv() 
        if TrackerCode(bye_request_pkt.action) == TrackerCode.BYE:
            self.close()
            logging.debug("Shutdown successful.")
        else:
            logging.debug("Shutdown unsuccessful.")
# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
