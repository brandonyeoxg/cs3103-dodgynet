from builtins import dict
from urllib.parse import urlparse
from random import randint
import socket
import struct
import time
from .TrackerException import TrackerRequestException, TrackerResponseException

"""according to http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html"""
DEFAULT_CONNECTION_ID = 0x41727101980
DEFAULT_TIMEOUT = 2

JOIN = 0
ANNOUNCE = 1
ERROR = 2


def parseurl(url):
    parsed = urlparse(url)
    return parsed.hostname, parsed.port


"""
    Tracker for working with udp based tracking protocol

    To initialise call

    tracker = UDPTracker(<url/localhost of initial seeder>, <timeout=2>, <infohash>)
    tracker.connect()
"""


class UdpTracker:
    announce_fields = [
        "peer_id",
        "downloaded",
        "left",
        "uploaded",
        "event",
        "ip_address",
        "num_want",
        "port"
    ]

    def __init__(self, initial_seeder_url):
        self.host, self.port = parseurl(initial_seeder_url)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_id = self.host
        self.connection_id = DEFAULT_CONNECTION_ID
        self.transactions = {}
        self.timeout = DEFAULT_TIMEOUT

    def send(self, action, payload=None):
        if not payload:
            payload = ''
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

    def announce(self):
        arguments = dict.fromkeys(self.announce_fields)
        arguments['peer_id'] = self.peer_id
        arguments['port'] = 6800
        arguments['num_want'] = 10
        values = [arguments[a] for a in self.announce_fields]
        payload = struct.pack('!20sQQQLLLH', *values)
        return self.send(ANNOUNCE, payload)

    def listen_for_response(self):
        self.sock.settimeout(self.timeout)
        try:
            response = self.sock.recv(10240)
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
            return self.process_join(payload)
        elif action == ANNOUNCE:
            return self.process_announce(payload)
        elif action == ERROR:
            return self.process_error(payload)

    def process_join(self, payload):
        self.connection_id = struct.unpack('!Q', payload)[0]
        return self.connection_id

    def process_announce(self, payload):
        info_struct = '!LLL'
        info_size = struct.calcsize(info_struct)
        info = payload[:info_size]
        interval, leechers, seeders = struct.unpack(info_struct, info)

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
                    leechers=leechers,
                    seeders=seeders,
                    peers=peers)

    def process_error(self, payload):
        message = struct.unpack('!8s', payload)
        raise TrackerResponseException('Error response', message)
