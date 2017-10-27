import sys
import os
import math
import Puncher
import signal
from UdpTrackerServer import *
from UdpTrackerClient import *
import Puncher
import endpoint

CHUNK_SIZE = 1024
#DEFAULT_PORT = 50818
DEFAULT_PUNCHER_A = ("127.0.0.1", 50818)

def main():

    clientType = sys.argv[1]
    option = sys.argv[2]

    if (clientType == "seed"):

        fileName = sys.argv[3]
        filesize = os.path.getsize(fileName)
        numChunks = math.ceil(filesize/CHUNK_SIZE)

        total_chunks = []
        for count in range(numChunks):
            total_chunks.append(count)

        if (option == "upload"):
            dirClient = Puncher.DirectoryClient()
            dirClient.new_file(fileName, total_chunks)
        
        # become seeder
        client = UdpTrackerClient("127.0.0.1", DEFAULT_PORT) #TODO change to file dir IP
        client.join()
        print (client.listen_for_response())

        chunk_have = NO_CHUNK
        for c in total_chunks:
            client.announce(NO_CHUNK, c)
        
        #init weakling protocol
        #get server inside
        #do wait loop until user terminates
        #tTODO
        c = []
        ep = endpoint.DummyEndpoint(DEFAULT_PUNCHER_A, fileName, []) #TODO change to puncher addr
        ep.start()

        # Wait until User terminates
        u_input = None
        while u_input!='Quit':
                u_input = input("Type Quit to stop seeding and quit the program:")

        print("Quitting!")

    elif (clientType == "leech" and option == "list"):
        # call dir client list, display results and quit
        dirClient = Puncher.DirectoryClient()
        listFiles = dirClient.list()

        for element in listFiles:
            print (element)


    elif (clientType == "leech" and option == "download"):
        #fileName = sys.argv[3]
        portNum = sys.argv[3]

        client = UdpTrackerClient("127.0.0.1", portNum) #TODO change to file directory ip
        client.join()
        #print (client.listen_for_response())
        resp = client.listen_for_response()
        print ('Connection: '+ resp['response']['completed'])
        total_chunks = resp['response']['chunk_list']


        chunk_have = NO_CHUNK
        total_chunks_remaining = []

        for c in total_chunks:
            total_chunks_remaining.append(c)

        ep = endpoint.DummyEndpoint(DEFAULT_PUNCHER_A, fileName, total_chunks_remaining, client) #TODO change to puncher addr
        ep.start()
        ep.get_input()

        
        print(client.shutdown()) # exit after completing file download

    else:
        print ("Usage:")
        print ("p2pclient seed upload/join <filename>")
        print ("p2pclient leech list")
        #print ("p2pclient leech query <filename>")
        print ("p2pclient leech download <filename>")

if __name__ == "__main__":
    main()
