import socket
import struct
import time
import json

def read_tweets():
    multicast_group = '232.1.1.1'
    server_address = ('', 1235)

    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    sock.bind(server_address)

    # Tell the operating system to add the socket to the multicast group
    # on all interfaces.
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Receive loop
    tweets = []
    t_end = time.time() + 20
    while time.time() < t_end:
        data, _ = sock.recvfrom(1024)
        tweets.append(data)

    sock.close()
    return tweets

def parse_tweets(tweets):
    pass