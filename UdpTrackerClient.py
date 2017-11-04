from builtins import dict
from random import randint
from enum import Enum
import ctypes as ct
import socket
import struct
import time
from UdpTrackerCommons import *
from TrackerException import TrackerRequestException, TrackerResponseException
import ipaddress

class TrackerCode(Enum):
    BYE = 0
    JOIN = 1
    ANNOUNCE = 2
    WANT = 3

class TrackerPacket(ct.Structure):
    _fields_ = [("connection_id", ct.c_ubyte * 8),
                ("action", ct.c_ubyte * 4),
                ("transaction_id", ct.c_uint),
                ("peer_id", ct.c_uint),
                ("ip", ct.c_ubyte * 4), # Represents in [Announce Request: Client IPv4] [Want Request: Client IPv4] [Want Response: Peer A IPv4]
                ("id", ct.c_uint), # Represents in [Announce Request: Num Chunk Have] [Want Request: Num Chunk Want] [Want Response: Peer A peer id]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return TrackerCode(self.action)
    def set_connection_id(self, connection_id):
        self.connection_id = connection_id
    def get_connection_id(self):
        return self.connection_id
    def set_transaction_id(self, transaction_id):
        self.transaction_id = transaction_id
    def get_transaction_id(self):
        return self.transaction_id
    def set_peer_id(self, peer):
        self.peer_id = peer;
    def get_peer_id(self):
        return self.peer_id
    def set_ip(self, ip):
        self.ip = ip
    def get_ip(self):
        return self.ip
    def set_id(self, id):
        self.id = id
    def get_variable_data2(self):
        return self.id
"""
    Tracker for working with udp based tracking protocol on the client side

    To initialise call

    tracker = UDPTracker(<url/localhost of initial seeder>, <timeout=2>, <infohash>)
    tracker.connect()
"""
class UdpTrackerClient:
    announce_fields = [
        "peer_id",
        "downloaded",
        "left",
        "uploaded",
        "event",
        "ip_address",
        "num_want",
        "port",
        "chunk_want",
        "chunk_have"
    ]

    def __init__(self, host = 'localhost', port = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_id = -1
        self.connection_id = DEFAULT_CONNECTION_ID
        self.transactions = {}
        self.timeout = 10000

    def send(self, action, payload=None):
        # maybe payload should not be handled here
        if not payload:
            payload = b''
        trans_id, header = self.build_header(action)
        self.transactions[trans_id] = trans = {
            'action': action,
            'time': time.time(),
            'payload': payload,
            'complete': False
        }
        print((self.host, self.port))
        self.sock.sendto(header + payload, (self.host, self.port))
        return trans

    def build_header(self, action):
        transaction_id = randint(0, 1 << 32 - 1)
        return transaction_id, struct.pack('!QLL', self.connection_id, action, transaction_id)

    def join(self):
        # can form a tracker packet here and send it into the send method
        # join_request_pkt = TrackerPacket()
        # join_request_pkt.set_connection_id(self.connection_id)
        # join_request_pkt.set_action(TrackerCode.JOIN)
        # join_request_pkt.set_transaction_id(randint(0, 1 << 32 - 1))
        # join_request_pkt.set_peer_id(-1)
        # return self.send(join_request_pkt)
        return self.send(JOIN)

    # can change this to (self, have_chunk_num)
    def announce(self, want_chunk_num = NO_CHUNK, have_chunk_num = NO_CHUNK):
        arguments = dict.fromkeys(self.announce_fields)
        arguments['peer_id'] = bytes(self.peer_id, 'utf-8')
        arguments['port'] = DEFAULT_PORT
        arguments['ip_address'] = int(ipaddress.ip_address(self.host))
        arguments['num_want'] = DEFAULT_PEERS_WANT
        arguments['chunk_want'] = want_chunk_num
        arguments['chunk_have'] = have_chunk_num
        for a in self.announce_fields:
            if arguments[a] is None:
                arguments[a] = 0
        values = [arguments[a] for a in self.announce_fields]
        payload = struct.pack('!20sQQQLLLHLL', *values)
        # can form a tracker packet here and send it into the send method
        # announce_request_pkt = TrackerPacket()
        # announce_request_pkt.set_connection_id(self.connection_id)
        # announce_request_pkt.set_action(TrackerCode.ANNOUNCE)
        # announce_request_pkt.set_transaction_id(randint(0, 1 << 32 - 1))
        # announce_request_pkt.set_peer_id(self.peer_id)
        # announce_request_pkt.set_ip(int(ipaddress.ip_address(self.host)))
        # announce_request_pkt.set_id(have_chunk_num)
        # return self.send(announce_request_pkt)
        return self.send(ANNOUNCE, payload)

    def want(self, want_chunk_num) :
        # can form a tracker packet here and send it into the send method
        # want_request_pkt = TrackerPacket()
        # want_request_pkt.set_connection_id(self.connection_id)
        # want_request_pkt.set_action(TrackerCode.ANNOUNCE)
        # want_request_pkt.set_transaction_id(randint(0, 1 << 32 - 1))
        # want_request_pkt.set_peer_id(self.peer_id)
        # want_request_pkt.set_ip(int(ipaddress.ip_address(self.host)))
        # announce_request_pkt.set_id(want_chunk_num)
        # return self.send(announce_request_pkt)

    def listen_for_response(self):
        #self.sock.settimeout(self.timeout)
        try:
            response = self.sock.recv(1024)
        except socket.timeout:
            return dict()
        # can be removed since the TrackerPacket has a standardised pkt of connection_id, action, transaction_id, peer_id
        headers = response[:8]
        payload = response[8:]
        action, trans_id = struct.unpack("!LL", headers)
        try:
            trans = self.transactions[trans_id]
        except KeyError:
            raise TrackerResponseException("Invalid Transaction: id not found", trans_id)
        # self.process can be changed to self.process(trackerPkt) where trackerPkt is TrackerPacket
        trans['response'] = self.process(action, payload)
        trans['completed'] = True
        del self.transactions[trans_id]
        return trans

    # instead of process(self, action, payload) perhaps can change to process(self, tracker_pkt)
    def process(self, action, payload):
        if action == JOIN:
            print("=========== Client process join ===========")
            return self.process_join(payload)
        elif action == ANNOUNCE:
            print("=========== Client process announce ===========")
            return self.process_announce(payload)
        #elif tracker_pkt.getAction() == TrackerCode.WANT:
        #   print("=========== Client process want ===========")
        #   return self.process_want(tracker_pkt)
        elif action == QUIT:
            print("=========== Client process quit ===========")
            return self.process_quit(payload)

    # instead of process_join(self, payload) perhaps can change to process_join(self, tracker_pkt)
    def process_join(self, payload):
        # these can be removed since we no longer need to track the chunk list line 178 to 191
        fixed_payload = payload[:28]
        chunk_data = payload[28:]

        chunk_size = struct.calcsize('!L')
        chunk_count = len(chunk_data) / chunk_size

        recv_chunk_list = []

        for chunk_offset in range(int(chunk_count)):
            off = chunk_size * chunk_offset
            chunk = chunk_data[off: off + chunk_size]
            chunk_num = struct.unpack('!L', chunk)[0]
            recv_chunk_list.append(chunk_num)

        # since this is a join protocol, we just need to obtain peer_id from tracker_pkt.get_peet_id
        self.connection_id, self.peer_id = struct.unpack('!Q20s', fixed_payload)
        self.peer_id = self.peer_id.decode('ascii').rstrip('\x00')
        return dict(conn_id=self.connection_id, peer_id=self.peer_id, chunk_list=recv_chunk_list)

    # instead of process_announce(self, payload) perhaps can change to process_announce(self, tracker_pkt)
    def process_announce(self, payload):
        info_struct = '!L'
        info_size = struct.calcsize(info_struct)
        info = payload[:info_size]
        interval = struct.unpack(info_struct, info)[0]
        peer_data = payload[info_size:]
        peer_struct = '!LH'
        peer_size = struct.calcsize(peer_struct)
        peer_count = len(peer_data) / peer_size
        peers = []
        # this is not need as we no longer receive any peers from he announce request, it is the want request that obtains the peers
        # process announce is just to receive the ACK from the server now
        for peer_offset in range(int(peer_count)):
            off = peer_size * peer_offset
            peer = peer_data[off:off + peer_size]
            addr, port = struct.unpack(peer_struct, peer)
            peers.append({
                'addr': socket.inet_ntoa(struct.pack('!L', addr)),
                'port': port
            })
        return dict(interval=interval,
                    peers=peers)

    def process_want(self, tracker_pkt):
        # peer = {'addr': tracker_pkt.get_ip, 'peer_id': tracker_pkt.get_peer_id}
        # return dict(peers=peers)

    def process_quit(self, payload):
        return dict(quit="True")

    def shutdown(self):
        #send shutdown to server
        self.send(QUIT)
        return self.listen_for_response()
