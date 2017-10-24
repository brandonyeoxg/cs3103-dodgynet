from UdpTrackerClient import *

client = UdpTrackerClient("127.0.0.1", DEFAULT_PORT)
client.join()
print (client.listen_for_response())

while True:
    client.announce()
    print (client.listen_for_response())
    time.sleep(120)