from urllib.parse import urlparse

# according to http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html
DEFAULT_CONNECTION_ID = 0x41727101980
DEFAULT_TIMEOUT = 120
DEFAULT_PORT = 6800
DEFAULT_PEERS = 1000
JOIN = 0
ANNOUNCE = 1
ERROR = 2


def parseurl(url):
    parsed = urlparse(url)
    return parsed.hostname, parsed.port
