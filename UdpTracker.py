from urllib.parse import urlparse
from random import randint
import socket
import struct
import time

"""according to http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html"""
DEFAULT_CONNECTION_ID = 0x41727101980
DEFAULT_TIMEOUT = 2

CONNECT = 0
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


    def build_header(self):
        transaction_id = randint(0, 1 << 32 - 1)
        return transaction_id, struct.pack('!QLL', self.connection_id, action, transaction_id)

    def join(self):
        return self.send(CONNECT)