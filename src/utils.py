import socket
import struct
import time
import json

class Thing():
    def __init__(self, id, space, address):
        self.id = id
        self.space = space
        self.address = address

class Service():
    def __init__(self, name: str, inputs: list, thing: Thing):
        self.name = name
        self.inputs = inputs
        self.thing = thing

    def exec(self):
        try:
            s = socket.socket()
        except socket.error as err:
            print('Socket error: ' + err)

        s.connect((self.thing.address, 6668))
        s.send(json.dumps({'Tweet Type':'Service Call', 
                           'Thing ID':self.thing.id, 
                           'Space ID':self.thing.space, 
                           'Service Name':self.name, 
                           'Service Inputs':'(' + ', '.join(str(input) for input in self.inputs) + ')'
                          }))
        s.close()

class Relationship():
    def __init__(self, service_1, service_2):
        pass

def read_tweets():
    multicast_group = '232.1.1.1'
    server_address = ('', 1235)

    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    s.bind(server_address)

    # Tell the operating system to add the socket to the multicast group
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Receive loop
    tweets = []
    t_end = time.time() + 20
    while time.time() < t_end:
        data, _ = s.recvfrom(1024)
        tweets.append(data)
    s.close()

    return tweets

# currently prints out service names 
# should return separate lists containing services things relationships
def parse_tweets(tweets: list):
    tweets = [json.loads(tweet) for tweet in tweets]
    for tweet in tweets:
        if tweet['Tweet Type'] == 'Service':
            print(tweet['Entity ID'] + ': ' + tweet['Name'])

if __name__ == '__main__':
    parse_tweets(read_tweets())