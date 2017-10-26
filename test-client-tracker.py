from UdpTrackerClient import *

client = UdpTrackerClient("127.0.0.1", DEFAULT_PORT)
client.join()
response = client.listen_for_response()
chunk_list = response['response']['chunk_list']
print (chunk_list)

fake_total_chunks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
chunk_have = NO_CHUNK
for chunk_num in fake_total_chunks:
    print ('Chunk want: ' + str(chunk_num))
    client.announce(chunk_num, chunk_have)
    response = client.listen_for_response()
    print(response)
    interval = response['response']['interval']
    peers = response['response']['peers']
    chunk_have = chunk_num
    time.sleep(interval)
client.announce(NO_CHUNK, chunk_have)
client.listen_for_response()
print(client.shutdown())
