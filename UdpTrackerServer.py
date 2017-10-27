import socket
import struct
import time
from ipaddress import ip_address
from UdpTrackerCommons import *
import threading

"""
    Tracker for working with udp based tracking protocol on the server side

    To initialise call

    tracker = UDPTracker(<url/localhost of initial seeder>, <timeout=2>, <infohash>)
    tracker.connect()
"""
DEFAULT_TIMEOUT = 1000

class UdpTrackerServer:
    connection_id = 0

    def __init__(self,
                 host: str = '',
                 port: int = DEFAULT_PORT,
                 refresh_interval: int = 300,
                 conn_valid_interval: int = DEFAULT_TIMEOUT,
                 chunk_have = []):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        hostname = self.get_public_ip()
	# DONT BIND to hostname
        self.sock.bind(('', port))
        self.peer_id = socket.gethostbyname(socket.gethostname())
        self.peer_list = [{'peer_id': 0, 'ip_addr': hostname, 'port': port, 'chunk_have': chunk_have}]
        self.chunk_list = chunk_have
        self.peer_list_ctr = 1
        self.connections = []
        self.addr = (host, port)
        self.refresh_interval = refresh_interval
        self.conn_valid_interval = conn_valid_interval

    def run_server_tracker(self):
        #self.cull_connections()
        print(self.listen_for_request())

    def get_public_ip(self):
        return socket.gethostbyname(self.host)

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

    def generatePeerId(self):
        output = self.peer_list_ctr
        self.peer_list_ctr += 1
        return output

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
            print("=========== Server handles join ===========")
            return self.process_join(addr, action, payload)
        elif action == ANNOUNCE:
            print("=========== Server handles announce ===========")
            return self.process_announce(addr, conn_id, action, payload)
        elif action == QUIT:
            print("=========== Server handles quit ===========")
            return self.process_quit(addr, conn_id, action, payload)

    def process_join(self, addr, action, payload):
        conn_id = self.generate_connection_id()
        transaction_id = struct.unpack('!L',payload)[0]
        peer_id = str(self.generatePeerId())
        new_payload = struct.pack('!Q', conn_id)
        peer_id_payload = struct.pack('20s', peer_id.encode())
        self.connections.append({'conn_id': conn_id, 'time': time.time(), 'peer_id': peer_id})
        packed_chunks = b''
        for chunk in self.chunk_list:
            packed_chunks = packed_chunks + struct.pack('!L', chunk)
        return self.send(addr, action, transaction_id, new_payload + peer_id_payload + packed_chunks)

    def process_announce(self, addr, conn_id, action, payload):
        for connection in self.connections:
            if connection['conn_id'] == conn_id:
                transaction_id, peer_id, download, left, uploaded, event, ip_addr, num_want, port, chunk_want, chunk_have \
                    = struct.unpack('!L20sQQQLLLHLL', payload)
                peer_id = peer_id.decode(encoding="UTF-8").rstrip('\x00')
                self.add_peer(peer_id, addr[0], addr[1])
                if chunk_have != NO_CHUNK:
                    self.update_peer_chunk(peer_id, chunk_have)
                interval = self.refresh_interval
                peers = b''
                if chunk_want != NO_CHUNK:
                    peers_with_chunk = self.get_peers_by_chunk_num(chunk_want)
                    peers = b''.join(
                        (ip_address(p['ip_addr']).packed + p['port'].to_bytes(length=2, byteorder='big'))
                        for p in peers_with_chunk)
                new_payload = struct.pack('!L', interval) + peers
                print("=========== Current peerlist: " + str(self.peer_list.__len__()) + " ===========")
                return self.send(addr, action, transaction_id, new_payload)
        return dict()

    def process_quit(self, addr, conn_id, action, payload):
        a = 0
        for conn in self.connections:
            if conn_id == conn['conn_id']:
                peer_id = conn['peer_id']
                self.delete_peer_from_list(peer_id)
                break
            a += 1
        del self.connections[a]
        transaction_id = struct.unpack('!L', payload)[0]
        return self.send(addr, action, transaction_id)

    def delete_peer_from_list(self, peer_id):
        a = 0
        for peer in self.peer_list:
            if peer['peer_id'] == peer_id:
                del peer
                break
            a += 1
        del self.peer_list[a]

    def add_peer(self, peer_id, ip_addr, port):
        if not self.peer_list:
            self.peer_list.append({'peer_id': peer_id, 'ip_addr': ip_addr, 'port': port, 'chunk_have': []})
        else:
            for peer in self.peer_list:
                if peer['peer_id'] == peer_id:
                    return
            self.peer_list.append({'peer_id': peer_id, 'ip_addr': ip_addr, 'port': port, 'chunk_have': []})
        return

    def update_peer_chunk(self, peer_id, chunk_have):
        for peer in self.peer_list:
            if peer['peer_id'] == peer_id:
                peer['chunk_have'].append(chunk_have)
                print("========= Peer " + str(peer['peer_id']) + " Chunks =========")
                print(peer['chunk_have'])

    def get_peers_by_chunk_num(self, chunk_want):
        peer_with_chunk = []
        for peer in self.peer_list:
            if chunk_want in peer['chunk_have']:
                peer_with_chunk.append({'ip_addr': peer['ip_addr'], 'port': peer['port']})
        return peer_with_chunk

    def shutdown(self):
        self.sock.shutdown()
