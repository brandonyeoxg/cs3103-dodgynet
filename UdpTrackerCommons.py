from urllib.parse import urlparse

# according to http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html
DEFAULT_CONNECTION_ID = 0x41727101980
DEFAULT_TIMEOUT = 1000
DEFAULT_PORT = 68760
DEFAULT_PEERS = 1000
DEFAULT_PEERS_WANT = 10

NO_CHUNK = 4294967295
JOIN = 0
ANNOUNCE = 1
QUIT = 2


def parseurl(url):
    parsed = urlparse(url)
    return parsed.hostname, parsed.port
