import socket
import struct
import time
from ipaddress import ip_address
from UdpTrackerCommons import *
import threading
import socketserver

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
        hostname = socket.gethostbyname(host)
        self.sock.bind((hostname, port))
        self.peer_id = socket.gethostbyname(socket.gethostname())
        self.peer_list = []
        self.connections = []
        self.addr = (host, port)
        self.refresh_interval = refresh_interval
        self.conn_valid_interval = conn_valid_interval

    def run_server_tracker(self):
        #self.cull_connections()
        print("waiting for connections")
        print(self.listen_for_request())

    def cull_connections(self):
        server_time = time.time()
        del_conns = []
        for connection in self.connections:
            print (connection)
            conn_time = float(connection['time'])
            delta_time = server_time - conn_time
            print ("delta time:" + str(delta_time))
            if (delta_time > DEFAULT_TIMEOUT):
                del_conns.append(connection["conn_id"])
        for connection in del_conns:
            del self.connections[connection["conn_id"]]


    def listen_for_request(self):
        request, addr = self.sock.recvfrom(1024)
        request_header = request[:12]
        payload = request[12:]
        conn_id = struct.unpack('!Q', request_header[:8])[0]
        action = struct.unpack('!L', request_header[8:])[0]

        trans = {'action': action, 'time': time.time(), 'payload': payload, 'complete': False}

        trans['response'] = self.process_request(addr, conn_id, action, payload)
        trans['completed'] = True

        return trans

    def send(self, addr, action, transaction_id, payload=None):
        print("Server sends data")
        if not payload:
            payload = b''
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
            print("Server handles join")
            return self.process_join(addr, action, payload)
        elif action == ANNOUNCE:
            print("Server handles announce")
            return self.process_announce(addr, conn_id, action, payload)

    def process_join(self,addr, action, payload):
        conn_id = self.generate_connection_id()
        transaction_id = struct.unpack('!L',payload)[0]
        new_payload = struct.pack('!Q', conn_id)
        self.connections.append({'conn_id':conn_id,'time':time.time()})
        print (self.connections)
        return self.send(addr, action, transaction_id, new_payload)

    def process_announce(self, addr, conn_id, action, payload):
        for connection in self.connections:
            if connection['conn_id'] == conn_id:
                transaction_id, peer_id, download, left, uploaded, event, ip_addr, num_want, port = struct.unpack('!L20sQQQLLLH', payload)
                self.add_peer(conn_id, addr[0], addr[1])
                interval = self.refresh_interval
                peers = b''.join(
                    (ip_address(p['ip_addr']).packed + p['port'].to_bytes(length=2, byteorder='big'))
                    for p in self.peer_list)

                new_payload = struct.pack('!Q', interval) + peers
                print("Current peerlist: " + str(self.peer_list.__len__()))
                return self.send(addr, action, transaction_id, new_payload)
        return dict()

    def add_peer(self, peer_id, ip_addr, port):
        if not self.peer_list:
            self.peer_list.append({'peer_id': peer_id, 'ip_addr': ip_addr, 'port': port})
        else:
            for peer in self.peer_list:
                if peer['peer_id'] == peer_id:
                    return
            self.peer_list.append({'peer_id': peer_id, 'ip_addr': ip_addr, 'port': port})
        return
