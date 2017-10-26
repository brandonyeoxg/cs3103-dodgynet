import queue
import threading
import pickle
from UdpTrackerServer import *
from UdpTrackerClient import *
from enum import Enum
import Puncher

CHUNK_SIZE = 1024

class ProtocolCodes(Enum):
    RECEIVE_REQUEST_FROM_PEER = 1
    SENDING_CHUNK_TO_PEER = 2


class P2pProtocol(object):

    @classmethod
    #def pack(cls, protocol, fileHash, fileName, chunkNum, data):
    def pack(cls, fileName, chunkNum):
        #chunk the file

        file = open(fileName, "rb")
        file.seek((chunkNum) * CHUNK_SIZE)
        dataBytes = file.read(CHUNK_SIZE)
        load = {
            'protocol' : ProtocolCodes.SENDING_CHUNK_TO_PEER,
            #'fileHash' : 0, #to change later
            #'fileName' : fileName,
            'chunkNum' : chunkNum,
            #hash
            'data' : dataBytes
        }
        packet = picke.dumps(load)

        return packet

    @classmethod
    def leechPack(cls, fileName, chunkNum):
        req = {
                'protocol' : ProtocolCodes.RECEIVE_REQUEST_FROM_PEER,
                'chunkWanted' : chunkNum
        }

    @classmethod
    def unpack(cls, data):
        response = pickle.loads(data)
        #filepath = response["filename"] + ".part" + str(response["chunkNum"])
        #file = open(filepath, "wb")
        #file.write(response["data"])
        #file.close()
        #chunkAvail.update({response["chunkNum"] : True})

        return response


class DummyEndpoint(object):
    def __init__(self, apuncher_addr, fileName, chunks_needed, clientObj=None):
        self.p_queue = queue.Queue()
        self.c_queue = queue.Queue()
        self.weaklingP = Puncher.WeaklingProtocol(apuncher_addr, self.p_queue, self.c_queue)
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
        self.fileName = fileName
        self.chunks_needed = chunks_needed
        self.totalChunks = len(chunks_needed)
        self.clientObj = clientObj

    def thread_job(self):
        while True:
            item = self.p_queue.get()

            if item == None:
                print("[Client] Endpoint Terminate")
                break
            data, addr = item
            #data = data.decode('utf-8')
            pickled = P2pProtocol.unpack(data)

            print("[Client] Data Unpacked: %s" % data)

            # seeder receving request
            if picked['protocol'] == ProtocolCodes.RECEIVE_REQUEST_FROM_PEER:
                
                packet = P2pProtocol.pack(fileName, pickled['chunkNum'])

                conn = self.weaklingP.client.connect(addr[0])
                conn.send(packet)


            # leecher receiving response
            elif picked['protocol'] == ProtocolCodes.SENDING_CHUNK_TO_PEER:

                #filepath = fileName + ".part" + str(picked['chunkNum'])
                #file = open(filepath, "wb")
                file = open(fileName, "ab")
                file.write(response["data"])
                file.close()

                chunks_needed.remove(picked['chunkNum'])
                #clientObj.announce(NO_CHUNK, chunkNum)

            '''
            if data == "Send me chunk 1.":
                print("[Client] Send Data[Here is chunk 1.]")
                conn = self.weaklingP.client.connect(addr[0])
                conn.send("Here is chunk 1.".encode('utf-8'))
            '''

    def start(self):
        self.t.start()
        self.weaklingP.start()

    def shutdown(self):
        print("[Client] Terminate Queue by put in None")
        self.p_queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)

    def get_input(self):
        while len(chunks_needed) > 0:

            for chunk_num in chunks_needed:

                print ('Chunk wanted: ' + str(chunk_num))
                #client.announce(NO_CHUNK, chunk_have)
                #response = client.listen_for_response()
                print(response)

                if len(response) > 0:
                    #interval = response['response']['interval']
                    peer_list = response['response']['peers']

                    #addr = peer_list[0]['addr'] 
                    addr = "127.0.0.1"

                    request = P2pProtocol.leechPack(fileName, chunk_num)

                    conn = self.weaklingP.client.connect(*addr)
                    conn.send(request)

                    time.sleep(1)



            '''
        while True:
            print(self.weaklingP.get_identity() + '>', end='', flush=True)
            data = sys.stdin.readline()
            if data == 'Q':
                break
            addr_raw = data.split(':')
            addr = (addr_raw[0], int(addr_raw[1]))
            print("[Client] Request chunk 1.")
            conn = self.weaklingP.client.connect(*addr)
            conn.send("Send me chunk 1.".encode('utf-8'))
            '''
            
            # Now we send data
            
            #self.c_queue.put(data)