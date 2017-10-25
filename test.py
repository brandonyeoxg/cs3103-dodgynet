import sys
import Puncher
import signal
from UdpTrackerServer import *
from UdpTrackerClient import *
import Puncher
import endpoint

def main():
    '''
    try:
        master = (sys.argv[1], int(sys.argv[2]))
    except (IndexError, ValueError):
        print >>sys.stderr, "usage: %s <host> <port> <pool>" % sys.argv[0]
        sys.exit(65)
    ep = None

    try:
        ep = Puncher.DummyEndpoint(master)
        ep.start()
        def handler(signal, frame):
            ep.shutdown()
            exit()
        signal.signal(signal.SIGINT, handler)
        ep.get_input()
    except (KeyboardInterrupt, SystemExit):
        print("Caught, Shutting down from main")
        ep.shutdown()
        exit()
    print("Exit!!")
    '''


    clientType = sys.argv[1]
    option = sys.argv[2]

    if (clientType == "seed"):
        if (option == "upload"):
            fileName = sys.argv[3]
            #runSeedUpload(fileName)
            dirClient = Puncher.DirectoryClient()

            #todo
            fake_total_chunks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            fileName = "hi"

            dirClient.new_file(fileName, fake_total_chunks)

        # become seeder
        client = UdpTrackerClient("127.0.0.1", DEFAULT_PORT)
        client.join()
        print (client.listen_for_response())

        fake_total_chunks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        chunk_have = NO_CHUNK
        for c in fake_total_chunks:
            client.announce(NO_CHUNK, c)
        
        #init weakling protocol
        #get server inside
        #do wait loop until user terminates
        #todo
        ep = endpoint.DummyEndpoint()
        ep.start()

    elif (clientType == "leech" and option == "list"):
        # call dir client list, display results and quit
        dirClient = Puncher.DirectoryClient()
        listFiles = dirClient.list()

        for element in listFiles:
            print (element)


    elif (clientType == "leech" and option == "query"):
        #fileName = sys.argv[3]
        portNum = sys.argv[3]

        ep = endpoint.DummyEndpoint()
        ep.start()

        client = UdpTrackerClient("127.0.0.1", portNum) #change to file directory ip
        client.join()
        print (client.listen_for_response())

        fake_total_chunks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        chunk_have = NO_CHUNK

        for chunk_num in fake_total_chunks:

            print ('Chunk want: ' + str(chunk_num))
            client.announce(NO_CHUNK, chunk_have)
            response = client.listen_for_response()
            print(response)
            interval = response['response']['interval']
            peer_list = response['response']['peer_list']

            peer_list[0]['addr'] 

            #connect to weakling client using ip address 
            
            chunk_have = chunk_num
            time.sleep(interval)

        client.announce(NO_CHUNK, chunk_have)
        client.listen_for_response()
        print(client.shutdown())

if __name__ == "__main__":
    main()
