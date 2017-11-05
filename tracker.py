from enum import Enum
import protocol
import ctypes as ct
import logging
from collections import defaultdict
import random

class TrackerCode(Enum):
    BYE = 0
    JOIN = 1
    ANNOUNCE = 2
    WANT = 3

WANT_NPEERS = 2

class TrackerPacket(ct.Structure):
    _fields_ = [("action", ct.c_uint),
                ("id", ct.c_uint)] # Represents in [Announce Request: Num Chunk Have] [Want Request: Num Chunk Want] [Want Response: Peer A peer id]
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
            str(self.id))

class TrackerServer(protocol.ThreadedTCPServer):
    def __init__(self, pub_addr):
        # addr refers to the listening for socket 
        addr=('', pub_addr[1])
        logging.debug("Initialize TrackerServer at tcp_port=%d" % addr[1])
        protocol.ThreadedTCPServer.__init__(self, addr, TrackerHandler, TrackerPacket)
        self.peer_lookup = {}
        self.chunk_map = defaultdict(set)
        self.peer_list_ctr = 0

class TrackerHandler(protocol.Handler):
    class Peer(object):
        def __init__(self, peer_id, addr):
            self.peer_id = peer_id
            self.addr = addr
            self.chunk_ids = set()
        def __str__(self):
            return "%s@%s-%s" % (self.peer_id, "%s:%d"%self.addr, str(self.chunk_ids))
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
    def handle(self):
        # data here
        peer = None
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
                r.id = peer_id
                self.send(r)
                peer = self.add_peer(peer_id)
                print(peer)
            elif action == TrackerCode.ANNOUNCE:
                logging.debug("Client announces that it has a particular chunk_id=%d" % r.id)
                if r.id in peer.chunk_ids:
                    logging.fatal("Client mentioned previously about chunk_id=%d, stop wasting my time." % r.id)
                    r.id  = 0
                    self.send(r)
                    continue
                if peer == None:
                    logging.fatal("Client failed to join before announcing.")
                    r.id  = 0
                    self.send(r)
                    continue
                self.update_peer_chunk(peer, r.id)
                self.send(r)
            elif action == TrackerCode.WANT:
                logging.debug("Client want chunk_id=%d" % r.id)
                if not r.id in self.server.chunk_map:
                    logging.fatal("Cannot find chunk_id=%d" % r.id)
                    r.id = 0
                    self.send(r)
                    continue
                if r.id in peer.chunk_ids:
                    logging.fatal("Client already have chunk_id=%d, stop wanting it." % r.id)
                    r.id = 0
                    self.send(r)
                    continue
                sel_peers = self.get_peers(r.id)
                for peer_id in sel_peers:
                    r.id = peer_id
                    self.send(r)
            else:
                logging.fatal("Unknown format, %s" % r)
            self.debug_print_active_peers()
        self.delete_peer(peer)
        self.debug_print_active_peers()
    def debug_print_active_peers(self):
        logging.debug("Active peers: [%s]" % ', '.join([ str(p) for p in self.server.peer_lookup.values()]) )
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)
    def delete_peer(self, peer):
        del self.server.peer_lookup[peer.peer_id]
        # Go to every chunk map and delete myself
        for chunk_id in peer.chunk_ids:
            self.server.chunk_map[chunk_id].remove(peer.peer_id) 
    def add_peer(self, peer_id):
        # we no longer need to track port so can remove
        self.server.peer_lookup[peer_id] = TrackerHandler.Peer(peer_id, self.client_address)
        return self.server.peer_lookup[peer_id]
    def update_peer_chunk(self, peer, chunk_id):
        peer.chunk_ids.add(chunk_id)
        self.server.chunk_map[chunk_id].add(peer.peer_id)
    def get_peers(self, chunk_id):
        peer_set = self.server.chunk_map[chunk_id]
        if len(peer_set) < WANT_NPEERS:
            return random.choices(list(peer_set), k=WANT_NPEERS)
        else:
            return random.sample(peer_set, WANT_NPEERS)
    def generatePeerId(self):
        self.server.peer_list_ctr += 1
        return self.server.peer_list_ctr
        
class TrackerClient(protocol.TCPClient):
    def __init__(self, server_addr):
        logging.debug("Starting TrackerClient.")
        protocol.TCPClient.__init__(self, server_addr, TrackerPacket)
    def join(self):
        # can form a tracker packet here and send it into the send method
        join_request_pkt = TrackerPacket()
        join_request_pkt.set_action(TrackerCode.JOIN)
        self.send(join_request_pkt)
        join_response_pkt = self.recv()
        if join_response_pkt.id != 0:
            logging.debug("Joined tracker network successfully, with id=%d" % join_response_pkt.id)
        else:
            logging.fatal("Failed to join tracker network.")
        self.peer_id = join_response_pkt.id
        return self.peer_id
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
    def announce(self, chunk_id):
        logging.debug("Peer announcing that it has chunk_id=%d." % chunk_id)
        announce_request_pkt = TrackerPacket()
        announce_request_pkt.set_action(TrackerCode.ANNOUNCE)
        announce_request_pkt.id = chunk_id
        self.send(announce_request_pkt)
        announce_response_pkt = self.recv()
        if announce_response_pkt.id == announce_request_pkt.id:
            logging.debug("Reporting that it has chunk_id=%s is successful." % chunk_id)
        else:
            logging.fatal("Failed to report chunk_id=%s" % chunk_id)
    def want(self, chunk_id):
        logging.debug("Peer want chunk_id=%d" % chunk_id)
        want_request_pkt = TrackerPacket()
        want_request_pkt.set_action(TrackerCode.WANT)
        want_request_pkt.id = chunk_id
        self.send(want_request_pkt)
        peer_ids = []
        for i in range(WANT_NPEERS):
            want_response_pkt = self.recv()
            if want_response_pkt.id == 0:
                logging.fatal("Cannot retrieve one of the peers.")
                continue
            peer_ids.append(want_response_pkt.id)
        return peer_ids
# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
