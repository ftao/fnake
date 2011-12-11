import time
import pickle
from agent import make_decision,build_graph


def test():
    with open('test.pickle', 'r') as f :
        data = pickle.load(f)
        start = time.time()
        make_decision(data['map'], data['info'], data['seq'])
        print 'cost', time.time() - start


test()
