import directory
import protocol

s = directory.DirPacket()
s.id = 0
print(protocol.debug_hex(bytearray(protocol.pack(s))))

dir_client = directory.DirClient()
#ss = dir_client.recv()
dir_client.send(s)
#print(ss.id)
dir_client.close()
