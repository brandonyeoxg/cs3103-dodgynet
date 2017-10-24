from builtins import dict
from random import randint
import socket
import struct
import time
from UdpTrackerCommons import *
from TrackerException import TrackerRequestException, TrackerResponseException
import ipaddress

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
        self.timeout = DEFAULT_TIMEOUT

    def send(self, action, payload=None):
        if not payload:
            payload = b''
        trans_id, header = self.build_header(action)
        self.transactions[trans_id] = trans = {
            'action': action,
            'time': time.time(),
            'payload': payload,
            'complete': False
        }
        self.sock.sendto(header + payload, (self.host, self.port))
        return trans

    def build_header(self, action):
        transaction_id = randint(0, 1 << 32 - 1)
        return transaction_id, struct.pack('!QLL', self.connection_id, action, transaction_id)

    def join(self):
        return self.send(JOIN)

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
        return self.send(ANNOUNCE, payload)

    def listen_for_response(self):
        self.sock.settimeout(self.timeout)
        try:
            response = self.sock.recv(1024)
        except socket.timeout:
            return dict()

        headers = response[:8]
        payload = response[8:]

        action, trans_id = struct.unpack("!LL", headers)

        try:
            trans = self.transactions[trans_id]
        except KeyError:
            raise TrackerResponseException("Invalid Transaction: id not found", trans_id)

        trans['response'] = self.process(action, payload)
        trans['completed'] = True
        del self.transactions[trans_id]
        return trans

    def process(self, action, payload):
        if action == JOIN:
            print("=========== Client process join ===========")
            return self.process_join(payload)
        elif action == ANNOUNCE:
            print("=========== Client process announce ===========")
            return self.process_announce(payload)
        elif action == ERROR:
            return self.process_error(payload)

    def process_join(self, payload):
        self.connection_id, self.peer_id = struct.unpack('!Q20s', payload)
        self.peer_id = self.peer_id.decode('ascii').rstrip('\x00')
        return dict(conn_id=self.connection_id, peer_id=self.peer_id)

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

    def process_error(self, payload):
        message = struct.unpack('!8s', payload)
        raise TrackerResponseException('Error response', message)
