#!/usr/bin/env python
import time
import sys
import pickle
import pprint
from agent import make_decision


def test(filename):
    with open(filename, 'r') as f :
        data = pickle.load(f)
        start = time.time()
        seq = None
        for i, snake in enumerate(data['info']['snakes']):
            if snake['name'] == data['name']:
                seq = i
#                snake['body'] = snake['body'][1:]
#                snake['length'] -=1
#                print snake['body']
                break
#            else:
#                snake['body'] = snake['body'][:1]
        #fake 
#        data['info']['eggs'].append((16,4))
#        pprint.pprint(data['info']['snakes'])
        print data['info']['snakes'][seq]['body']
        d = make_decision(data['map'], data['info'], seq)
        print 'd is ', d
        print 'cost', time.time() - start


test(sys.argv[1])
