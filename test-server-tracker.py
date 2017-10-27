from UdpTrackerServer import *

looping = True
HOST = "localhost"
print("Started listening on %s" % str(DEFAULT_PORT))

try:
    fake_total_chunks = [0]
    # <localhost> == seeders public ip 
    server = UdpTrackerServer('localhost',
                              DEFAULT_PORT,
                              1, DEFAULT_TIMEOUT,
                              fake_total_chunks)
    while looping:
        print ('server listening')
        server.run_server_tracker()

except KeyboardInterrupt:
    looping = False

finally:
    server.shutdown()
