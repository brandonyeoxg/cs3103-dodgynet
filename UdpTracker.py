from urllib.parse import urlparse
import socket

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
    def __init__(self, initialSeederUrl):
        self.host, self.port = parseurl(initialSeederUrl)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)