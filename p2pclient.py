import socket
import threading
import time
import sys
import pickle

CHUNK_SIZE = 1024
global chunkAvail = {}

class ProtocolCodes(Enum):
	SENDING_CHUNK_TO_PEER = 1


class P2pProtocol(object):

	@classmethod
	#def pack(cls, protocol, fileHash, fileName, chunkNum, data):
	def pack(cls, fileName, chunkNum):
		#chunk the file

		file = open(fileName, "rb")
		file.seek((chunkNum-1) * CHUNK_SIZE)
		dataBytes = file.read(CHUNK_SIZE)
		load = {
			'protocol' : ProtocolCodes.SENDING_CHUNK_TO_PEER,
			'fileHash' : 0, #to change later
			'fileName' : "test",
			'chunkNum' : chunkNum,
			#hash
			'data' : dataBytes
		}
		packet = picke.dumps(load)

		return packet

	@classmethod
	def unpack(cls, data):
		response = pickle.loads(data)
		#filepath = response["filename"] + ".part" + str(response["chunkNum"])
		#file = open(filepath, "wb")
		#file.write(response["data"])
		#file.close()
		#chunkAvail.update({response["chunkNum"] : True})

		return response


# leecher =======================================


def notifyChunksWanted():




# seeder ========================================

def runSeedUpload(fileName):




def generateTorrent(fileName):
	filesize = os.path.getsize(fileName)
	numChunks = math.ceil(filesize/CHUNK_SIZE) # let's just set it at 1024 for now
	#chunkHash = {}
	#chunkNum = 1
	#file = open(fileName, "rb")
	load = {
		'fileName' : fileName,
		'numChunks' : numChunks
	}

# ==============================================
def showUsage():
	print ("Usage: ")
	print ("p2pclient seed upload/join <filename>")
	print ("p2pclient leech list")
	print ("p2pclient leech query <filename>")
	print ("p2pclient leech download <filename>")


clientType = sys.argv[1]
option = sys.argv[2]

if (clientType == "seed" and option == "upload"):
	fileName = sys.argv[3]
	runSeedUpload(fileName)

elif (clientType == "seed" and option == "join"):
	fileName = sys.argv[3]
	runSeedJoin(fileName)

elif (clientType == "leech" and option == "list"):
	runLeechList()

elif (clientType == "leech" and option == "query"):
	fileName = sys.argv[3]
	runLeechQuery(fileName)

