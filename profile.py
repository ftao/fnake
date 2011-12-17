#!/usr/bin/env python
import time
import pickle
from agent import make_decision


def test():
    with open('live-1704.pickle', 'r') as f :
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
        d = make_decision(data['map'], data['info'], seq)
        print 'd is ', d
        print 'cost', time.time() - start


test()
