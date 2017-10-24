from UdpTrackerServer import *

looping = True
HOST = "localhost"

try:
    server = UdpTrackerServer()
    while looping:
        print ('server listening')
        server.run_server_tracker()

except KeyboardInterrupt:
    looping = False
