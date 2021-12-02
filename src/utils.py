import socket
import struct
import time
import json
import pickle


class Thing():
    def __init__(self, id, space, address):
        self.id = id
        self.space = space
        self.address = address

    def __str__(self):
        return f'Thing(id={self.id}, space={self.space}, ip={self.address})'


class Service():
    def __init__(self, name: str, input_count: list, has_output: bool, thing: Thing):
        self.name = name
        self.argc = input_count
        self.has_output = has_output
        self.thing = thing

    def exec(self, inputs):
        if len(inputs) != self.argc:
            print(f'Incorrect number of arguments for {self.name}: expected {self.argc}, recieved {len(inputs)}')
            return

        try:
            s = socket.socket()
        except socket.error as err:
            print('Socket error: ' + err)

        s.connect((self.thing.address, 6668))
        s.send(bytes(json.dumps({'Tweet Type':'Service Call', 
                           'Thing ID':self.thing.id, 
                           'Space ID':self.thing.space, 
                           'Service Name':self.name, 
                           'Service Inputs':'(' + ', '.join(str(input) for input in inputs) + ')'
                          }), 'ascii'))
        output = None
        if self.has_output:
            data = json.loads(s.recv(1024))
            output = data['Service Result']

        s.close()
        return output

    def __str__(self): 
        return f'Service(name={self.name}, argc={self.argc}, has_output={self.has_output}, thing={str(self.thing)})'


class Relationship():
    class Cooperative():
        class Control():
            def __init__(self, A: Service, B: Service):
                self.A = A if A.has_output else None
                self.B = B
            
            def exec(self, A_input, B_input, condition):
                if self.A != None:
                    result = self.A.exec(A_input)
                    if condition(result):
                        print('Output of A satisfies condition, executing B...')
                        return self.B.exec(B_input)
                    else:
                        print('Output of A does not satisfy condition.')
                else:
                    print(f'Service A cannot control B since it does not output.')

        class Drive():
            def __init__(self, A: Service, B: Service):
                self.A = A if A.has_output else None
                self.B = B
            
            def exec(self, A_input):
                if self.A != None:
                    result = self.A.exec(A_input)
                    return self.B.exec([int(result)])
                else:
                    print(f'Service A cannot drive B since it does not output.')

        class Support():
            def __init__(self, A: Service, B: Service):
                self.A = A
                self.B = B

            def exec(self, A_input, B_input):
                if self.A.has_output:
                    result = self.A.exec(A_input)
                    if result == 0:
                        return self.B.exec(B_input)
                    else:
                        return result
                else:
                    self.A.exec(A_input)
                    return self.B.exec(B_input)

        class Extend():
            def __init__(self, A: Service, B: Service):
                self.A = A
                self.B = B

            def exec(self, input):
                self.A.exec(input[:self.A.argc])
                return self.B.exec(input[self.A.argc:self.A.argc+self.B.argc])

    # Competitve relationships update the execution path
    class Competitive():
        # If this relationship is defined, the two services cannot both be in the rest,
        # as they either Contest (provide  mutually exclusive solutions for the same problem) 
        # or Interfere (services are insecure if they coexist at same time/space)
        class Block():
            def __init__(self, A: Service, B: Service):
                self.A = A
                self.B = B
        # If this relationship is defined futher instances of the invocation of A run B
        class Replace():
            def __init__(self, A: Service, B: Service):
                self.A = A
                self.B = B



def listen_for_json():
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

    data, _ = s.recvfrom(1024)
    recv_time = time.time()
    print('Heard First')
    tweets.append(data)

    while True:
        data, _ = s.recvfrom(1024)
        if data not in tweets:
            tweets.append(data)
        print('time since last ', time.time() - recv_time)
        if time.time() - recv_time > 5:
            break
        recv_time = time.time()

    s.close()

    return [tweet.decode('ascii') for tweet in tweets]


def json_to_tweet(tweet):
    contains = tweet.find('"API"')
    if contains > -1:
        end = tweet.find('"Type"')
        d = json.loads(tweet[:contains] + tweet[end:])
        d['API'] = tweet[contains+9:end-2]
        return d
    else:
        return json.loads(tweet)


def tweets_to_services(tweets: list):
    things = tweets_to_things(tweets)
    thing_ids = {t.id:t for t in things}

    return [Service(tweet['Name'], tweet['API'][tweet['API'].find('[')+1:tweet['API'].find(']')].count(',') // 2, 'Output' in tweet['API'], thing_ids[tweet['Thing ID']]) 
                       for tweet in filter(lambda x: x['Tweet Type'] == 'Service', tweets) 
                       if tweet['Thing ID'] in thing_ids]


def tweets_to_things(tweets: list):
    return [Thing(t['Thing ID'], t['Space ID'], '192.168.0.67' if t['Thing ID'] == 'RaspberryPi' else '192.168.0.180') 
           for t in filter(lambda x: x['Tweet Type'] == 'Identity_Language', tweets)]


if __name__ == '__main__':
    iden_lang_tweet = '{ "Tweet Type" : "Identity_Language","Thing ID" : "RaspberryPi","Space ID" : "MySmartSpace","Network Name" : "MySpaceNetwork","Communication Language" : "","IP" : "65.116.108.97","Port" : "6668" }'
    service_tweet1 = '{ "Tweet Type" : "Service","Name" : "alarm","Thing ID" : "RaspberryPi","Entity ID" : "Alarm","Space ID" : "MySmartSpace","Vendor" : "","API" : "alarm:[NULL]:(NULL)","Type" : "","AppCategory" : "","Description" : "Chimes buzzer three times","Keywords" : "" }'
    service_tweet2 = '{ "Tweet Type" : "Service","Name" : "nightlight","Thing ID" : "RaspberryPi","Entity ID" : "LED","Space ID" : "MySmartSpace","Vendor" : "","API" : "nightlight:["wait_time",int, NULL]:(NULL)","Type" : "","AppCategory" : "","Description" : "Keeps light on for specified number of seconds","Keywords" : "" }'
    service_tweet3 = '{ "Tweet Type" : "Service","Name" : "distance","Thing ID" : "RaspberryPi","Entity ID" : "Ultrasonic","Space ID" : "MySmartSpace","Vendor" : "","API" : "distance:[NULL]:(Output,int, NULL)","Type" : "","AppCategory" : "","Description" : "Get distance between sensor and facing object in centimeters","Keywords" : "" }'
    # tweet = json_to_tweet(tweet)
    # Service(tweet['Name'], tweet['API'].count(',') // 2, Thing('RaspberryPi', 'MySmartSpace', '192.168.0.67')).exec([])
    # services = tweets_to_services([json_to_tweet(t) for t in listen_for_json()])
    with open('services.txt', 'rb') as f:
        services = pickle.load(f)
    # for s in services:
    #     print(str(s))
        # if s.name == 'alarm':
        #     print('Running alarm')
        #     s.exec([])
        # if s.name == 'nightlight':
        #     print('Running nightlight')
        #     s.exec([3])
        # if s.name == 'distance':
        #     print('Running distance')
        #     print(s.exec([]))
    for s in services:
        if s.name == 'distance':
            service_A = s
        if s.name == 'alarm':
            service_B = s
    
    Relationship.Cooperative.Control(service_A, service_B).exec([], [], lambda x: int(x) > 100)


