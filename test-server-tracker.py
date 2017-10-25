from UdpTrackerServer import *

looping = True
HOST = "localhost"

try:
    fake_total_chunks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
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