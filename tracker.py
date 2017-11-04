from enum import Enum
import protocol
import ctypes as ct

class TrackerCode(Enum):
    BYE = 0
    JOIN = 1
    ANNOUNCE = 2
    WANT = 3

PORT = 60760
PUB_IP = "127.0.0.1"

class TrackerPacket(ct.Structure):
    _fields_ = [("connection_id", ct.c_ubyte * 8),
                ("action", ct.c_ubyte * 4),
                ("transaction_id", ct.c_uint),
                ("peer_id", ct.c_uint),
                ("ip", ct.c_ubyte * 4), # Represents in [Announce Request: Client IPv4] [Want Request: Client IPv4] [Want Response: Peer A IPv4]
                ("id", ct.c_uint)] # Represents in [Announce Request: Num Chunk Have] [Want Request: Num Chunk Want] [Want Response: Peer A peer id]
    def set_action(self, action):
        self.action = action.value
    def get_action(self):
        return TrackerCode(self.action)
    def set_addr(self, addr):
        self.ip = protocol.pack_ip(addr[0])
        self.port = addr[1]
    def get_addr(self):
        return (protocol.unpack_ip(self.ip), self.port)

class TrackerServer(protocol.ThreadedTCPServer):
    def __init__(self, pub_ip=PUB_IP, addr=('', PORT)):
        protocol.ThreadedTCPServer.__init__(self, addr, TrackerHandler, TrackerPacket)

class Handler(protocol.Handler):
    def setup(self):
        logging.debug("Connected %s:%d" % self.client_address)
        # STUB
        self.peer_list = None
        self.peer_list_ctr = None
    def handle(self):
        # data here
        while True:
            r = self.recv()
            action = r.get_action()
            if action == TrackerCode.BYE:
                logging.debug("Client says bye, we say bye back and quit!")
                a = 0
                for conn in self.connections:
                    if conn_id == conn['conn_id']:
                        peer_id = conn['peer_id']
                        self.delete_peer_from_list(peer_id)
                        break
                    a += 1
                del self.connections[a]
                self.send(r)
            elif action == TrackerCode.JOIN:
                logging.debug("Client wants to join the network.")
            elif action == TrackerCode.ANNOUNCE:
                logging.debug("Client announces that it has a particular chunk.")
            elif action == TrackerCode.WANT:
                logging.debug("Client says bye, we say bye back and quit!")
    def finish(self):
        logging.debug("Disconnected %s:%d" % self.client_address)
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
            self.peer_list.append({'peer_id':peer_id, 'ip_addr':ip_addr, 'port':port, 'chunk_have':[]})
        else:
            for peer in self.peer_list:
                if peer['peer_id'] == peer_id:
                    return
            # we no longer need to track port, so can remove
            self.peer_list.append({'peer_id':peer_id, 'ip_addr':ip_addr, 'port':port, 'chunk_have':[]})
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
    def generatePeerId(self):
        output = self.peer_list_ctr
        self.peer_list_ctr += 1
        return output
        
# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
