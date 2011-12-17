#!/usr/bin/env python
import time
import pickle
from agent import make_decision


def test():
    with open('live-1642.pickle', 'r') as f :
        data = pickle.load(f)
        start = time.time()
        seq = None
        for i, snake in enumerate(data['info']['snakes']):
            if snake['name'] == data['name']:
                seq = i
                print snake
                break
        d = make_decision(data['map'], data['info'], seq)
        print 'd is ', d
        print 'cost', time.time() - start


test()
