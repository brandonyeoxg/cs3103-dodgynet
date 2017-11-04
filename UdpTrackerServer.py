from enum import Enum
import ctypes as ct
import socket
import struct
import time
from ipaddress import ip_address
from UdpTrackerCommons import *
import threading

class TrackerCode(Enum):
    BYE = 0
    JOIN = 1
    ANNOUNCE = 2
    WANT = 3

class TrackerPacket(ct.Structure):
    _fields_ = [("connection_id", ct.c_ubyte * 8),
                ("action", ct.c_ubyte * 4),
                ("transaction_id", ct.c_uint),
                ("peer_id", ct.c_uint),
                ("ip", ct.c_ubyte * 4), # Represents in [Announce Request: Client IPv4] [Want Request: Client IPv4] [Want Response: Peer A IPv4]
                ("id", ct.c_uint), # Represents in [Announce Request: Num Chunk Have] [Want Request: Num Chunk Want] [Want Response: Peer A peer id]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return TrackerCode(self.action)
    def set_connection_id(self, connection_id):
        self.connection_id = connection_id
    def get_connection_id(self):
        return self.connection_id
    def set_transaction_id(self, transaction_id):
        self.transaction_id = transaction_id
    def get_transaction_id(self):
        return self.transaction_id
    def set_peer_id(self, peer):
        self.peer_id = peer;
    def get_peer_id(self):
        return self.peer_id
    def set_ip(self, ip):
        self.ip = ip
    def get_ip(self):
        return self.ip
    def set_id(self, id):
        self.id = id
    def get_variable_data2(self):
        return self.id

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
        # peer list at line 85 can be removed here
        self.peer_list = [{'peer_id': 0, 'ip_addr': hostname, 'port': port, 'chunk_have': chunk_have}]
        self.peer_list = []
        # chunk list can be removed
        self.chunk_list = chunk_have
        self.peer_list_ctr = 1
        self.connections = []
        self.addr = (host, port)
        # refresh interval and conn_valid_interval can be removed
        self.refresh_interval = refresh_interval
        self.conn_valid_interval = conn_valid_interval

    def run_server_tracker(self):
        #self.cull_connections()
        print(self.listen_for_request())

    def get_public_ip(self):
        return socket.gethostbyname(self.host)

    # cull connection can be removed since it is not being used
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
        print("Request from %s " % str((request, addr)))
        # this code chunk tries to find connection_id, transaction_id and action (based on TrackerPacket)
        # therefore we should deserialise connection_id, action, transaction, peer_id (based on TrackerPacket)
        request_header = request[:12]
        payload = request[12:]
        conn_id = struct.unpack('!Q', request_header[:8])[0]
        action = struct.unpack('!L', request_header[8:])[0]
        trans = {'action': action, 'time': time.time(), 'payload': payload, 'complete': False}
        # This code is the one that processes the request maybe can just pass the entire TrackerPacket inside
        trans['response'] = self.process_request(addr, conn_id, action, payload)
        trans['completed'] = True
        return trans

    def send(self, addr, action, transaction_id, payload=None):
        #this entire payload thing can be removed since everything is abstracted into TrackerPacket
        if not payload:
            payload = b''
        trans = {
            'action': action,
            'time': time.time(),
            'payload': payload,
            'complete': False
        }
        # we can standardise this by packing connection_id,action, transaction_id, peer_id
        # perhaps this packing should be done on another method layer not in this method
        header = struct.pack('!LL', action, transaction_id)
        self.sock.sendto(header + payload, addr)
        return trans

    def generate_connection_id(self):
        output = self.connection_id
        self.connection_id = self.connection_id + 1
        if self.connection_id > DEFAULT_PEERS:
            self.connection_id = 0
        return output

    # can be just changed to (self, addr, tracker_pkt)
    def process_request(self, addr, conn_id, action, payload):
        if action == JOIN:
            print("=========== Server handles join ===========")
            return self.process_join(addr, action, payload)
        elif action == ANNOUNCE:
            print("=========== Server handles announce ===========")
            return self.process_announce(addr, conn_id, action, payload)
        # where packet represents TrackerPacket
        #elif packet.getAction() == TrackerPacket.WANT:
        #    print("=========== Server handles want ===========")
        #    return self.process_want(addr, packet)
        elif action == QUIT:
            print("=========== Server handles quit ===========")
            return self.process_quit(addr, conn_id, action, payload)

    # can be just changed to (self, addr, tracker_pkt)
    def process_join(self, addr, action, payload):
        conn_id = self.generate_connection_id()
        transaction_id = struct.unpack('!L',payload)[0]
        peer_id = str(self.generatePeerId())
        new_payload = struct.pack('!Q', conn_id)
        peer_id_payload = struct.pack('20s', peer_id.encode())
        self.connections.append({'conn_id': conn_id, 'time': time.time(), 'peer_id': peer_id})
        packed_chunks = b''
        # no longer needed to send chunk list back since we have .torrent file.
        for chunk in self.chunk_list:
            packed_chunks = packed_chunks + struct.pack('!L', chunk)
        # the last param in the self.send is appending all of the packed binary code
        # we should pack conn_id, action, transaction_id, peer_id
        return self.send(addr, action, transaction_id, new_payload + peer_id_payload + packed_chunks)

    # can be just changed to (self, addr, tracker_pkt)
    def process_announce(self, addr, conn_id, action, payload):
        #checks every active connection on the server
        for connection in self.connections:
            # find the correct connection_id of the client
            if connection['conn_id'] == conn_id:
                # there would be no payload here as the announce request pkt contains only connection_id, transaction_id, action and peer_id
                transaction_id, peer_id, download, left, uploaded, event, ip_addr, num_want, port, chunk_want, chunk_have \
                    = struct.unpack('!L20sQQQLLLHLL', payload)
                peer_id = peer_id.decode(encoding="UTF-8").rstrip('\x00')
                # no longer need to take in the port number
                # need to remove the third param
                self.add_peer(peer_id, addr[0], addr[1])
                # this if stmt can be removed since process_announce is separated into announce(have chunk) and want(want chunk)
                if chunk_have != NO_CHUNK:
                    # this code still must remain as it updates the chunks that each peer has
                    self.update_peer_chunk(peer_id, chunk_have)
                # no need for interval as we do not use it in dodgynet
                interval = self.refresh_interval
                peers = b''
                # this entire if stmt chunk can be removed as it is handled in the process_want
                if chunk_want != NO_CHUNK:
                    peers_with_chunk = self.get_peers_by_chunk_num(chunk_want)
                    peers = b''.join(
                        (ip_address(p['ip_addr']).packed + p['port'].to_bytes(length=2, byteorder='big'))
                        for p in peers_with_chunk)
                new_payload = struct.pack('!L', interval) + peers
                print("=========== Current peerlist: " + str(self.peer_list.__len__()) + " ===========")
                # we can just send back connection_id, transaction_id, action, peer_id (based on TrackerPacket)
                return self.send(addr, action, transaction_id, new_payload)
        return dict()

    #  handles the clients wanting certain chunks
    def process_want(self, addr, tracker_pkt):
    #     #checks every active connection on the server
    #     for connection in self.connections:
    #         # find the correct connection_id of the client
    #         if connection['conn_id'] == conn_id:
    #             peers_with_chunk = self.get_peers_by_chunk_num(tracker_pkt.get_id()) # get_id to obtain chunk_want on a want request pkt
    #             if not peers_with_chunk:
    #                 return
    #             send_announce_pkt1 = TrackerPacket(tracker_pkt) # not too sure if there is a copy constructor in python, since connection_id, actiom, transaction_id and peer_id remains the same
    #             send_announce_pkt1.set_ip(peers_with_chunk[0]['ip_addr'])
    #             send_announce_pkt1.set_id(peers_with_chunk[0]['peer_id'])
    #             self.send(addr,send_announce_pkt1)
    #             if len(peers_with_chunk) is 1:
    #                 self.send(addr,send_announce_pkt1)
    #                 return
    #             send_announce_pkt2 = Tracker(tracker_pkt) # not too sure if there is a copy constructor in python, since connection_id, actiom, transaction_id and peer_id remains the same
    #             send_announce_pkt2.set_ip(peers_with_chunk[1]['ip_addr'])
    #             send_announce_pkt2.set_id(peers_with_chunk[1]['peer_id'])
    #             self.send(addr, send_announce_pkt2)

    # can be just changed to (self, addr, tracker_pkt)
    def process_quit(self, addr, conn_id, action, payload):
        a = 0
        for conn in self.connections:
            if conn_id == conn['conn_id']:
                peer_id = conn['peer_id']
                self.delete_peer_from_list(peer_id)
                break
            a += 1
        del self.connections[a]
        # this is basically sending a quit ack back to client.
        # can use the standard headers from TrackerPacket
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
            # we no longer need to track port so can remove
            self.peer_list.append({'peer_id': peer_id, 'ip_addr': ip_addr, 'port': port, 'chunk_have': []})
        else:
            for peer in self.peer_list:
                if peer['peer_id'] == peer_id:
                    return
            # we no longer need to track port, so can remove
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
                # remove port, replace it with peer_id of the client
                peer_with_chunk.append({'ip_addr': peer['ip_addr'], 'port': peer['port']})
        return peer_with_chunk

    def shutdown(self):
        self.sock.shutdown()
