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

    tracker = UDPTracker(<url/localhost if initial seeder>, <timeout=2>, <infohash>)
    tracker.connect()
"""
class UdpTracker:
    def __init__(self, initial_seeder_url):
        self.host, self.port = parseurl(initial_seeder_url)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_id = self.host
        self.connection_id = DEFAULT_CONNECTION_ID
        self.transactions = {}
        self.timeout = DEFAULT_TIMEOUT

    def send(self, action, payload = ''):
        trans_id, header = self.build_header(action)
        self.transactions[trans_id] = trans = {
            'action' : action,
            'time' : time.time(),
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

        trans['response'] = self.process(action, payload, trans)

    def process(self, action, payload, trans):
        if action == JOIN:
            return self.process_join(payload, trans)
        #elif action == ANNOUNCE:
         #   return self.process_announce(payload, trans)
        elif action == ERROR:
            return self.process_error(payload, trans)

    def process_join(self, payload, trans):
        self.connection_id = struct.unpack('!Q', payload)[0]
        return self.connection_id

