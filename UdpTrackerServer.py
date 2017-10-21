import socket
import struct
import time
from ipaddress import ip_address
from .UdpTrackerCommons import *

"""
    Tracker for working with udp based tracking protocol on the server side

    To initialise call

    tracker = UDPTracker(<url/localhost of initial seeder>, <timeout=2>, <infohash>)
    tracker.connect()
"""
class UdpTrackerServer:
    connection_id = 0

    def __init__(self,
                 host: str = 'localhost',
                 port: int = DEFAULT_PORT,
                 refresh_interval: int = 300,
                 conn_valid_interval: int = DEFAULT_TIMEOUT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_id = socket.gethostbyname(socket.gethostname())
        self.peer_list = []
        self.connections = []
        self.addr = (host, port)
        self.refresh_interval = refresh_interval
        self.conn_valid_interval = conn_valid_interval

    def run_server_tracker(self):
        self.cull_connections()
        self.listen_for_request()

    def cull_connections(self):
        server_time = time.time()
        del_conns = []
        for connection in self.connections:
            conn_time = connection['time']
            delta_time = conn_time - server_time
            if (delta_time > DEFAULT_TIMEOUT):
                del_conns.append(connection['conn_id'])
        for connection in self.connections:
            del self.connections[connection['conn_id']]


    def listen_for_request(self):
        request, addr = self.sock.recvfrom(10240)
        request_header = request[:12]
        payload = request[12:]
        conn_id = request_header[:8]
        action = request_header[8:]

        trans = []
        trans['response'] = self.process_request(action, conn_id, payload)
        trans['completed'] = True
        return trans

    def send(self, addr, action, transaction_id, payload=None):
        if not payload:
            payload = ''
        trans = {
            'action': action,
            'time': time.time(),
            'payload': payload,
            'complete': False
        }
        header = struct.pack('!LL', action, transaction_id)
        self.sock.sendto(header + payload, addr)
        return trans

    def generate_connection_id(self):
        output = self.connection_id
        self.connection_id = self.connection_id + 1
        if self.connection_id > DEFAULT_PEERS:
            self.connection_id = 0
        return output

    def process_request(self, addr, conn_id, action, payload):
        if action == JOIN:
            return self.process_join(addr, action, payload)
        elif action == ANNOUNCE:
            return self.process_announce(addr, conn_id, action, payload)

    def process_join(self,addr, action, payload):
        conn_id = self.generate_connection_id()
        transaction_id = payload
        new_payload = struct.pack('!Q', conn_id)
        self.connections[conn_id] = {'conn_id':conn_id,'time':time.time()}
        return self.send(addr, action, transaction_id, new_payload)

    def process_announce(self, addr, conn_id, action, payload):
        if conn_id in self.connections is True:
            transaction_id, peer_id, download, left, uploaded, event, ip_addr, num_want, port = struct.unpack('!L20sQQQLLLH', payload)
            if conn_id in self.peer_list is False:
                self.peer_list[conn_id] = {'peer_id':peer_id,'ip_addr':ip_addr, 'port':port}
            interval = self.refresh_interval

            peers = b''.join(
                (ip_address(p['ip_addr']).packed + p['port'].to_bytes(length=2, byteorder='big'))
                for p in self.peer_list)

            new_payload = struct.pack('!Q', interval) + peers
            return self.send((ip_addr, port), action, transaction_id, new_payload)