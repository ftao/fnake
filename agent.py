#!/usr/bin/env python
#coding=utf8
import sys
import random
import time
import copy 
import itertools
import logging
from collections import deque
from dijkstra import shortestPathFromDP

DUMPED = False
def dump_info(func):
    def wrap(map, info, seq):
        global DUMPED
        if not DUMPED:
            import pickle
            with open('test.ruby.pickle', 'w') as f:
                pickle.dump({'map' : map, 'info' : info, 'seq' : seq}, f)
            DUMPED = True
        return func(map, info, seq)
    return wrap

from fnake import Fnake, run_ai
from dijkstra import shortestPath,Dijkstra
from ailib import cmd_run, DIRECT, SPRIT_COMMAND

SPRINT_ROUND = 5 
SPRINT_STEP = 3 # sprint的时候, 每轮可以走的步数
SPRINT_REST = 20 # sprint之后需要休息的时间

direction_delta = [
    (-1, 0),
    (0, -1),
    (1, 0),
    (0, 1),
]

def point_add(size, x, y):
    return ((x[0] + y[0]) % size[0], (x[1] + y[1]) % size[1])

def is_near(size, x, y):
    for d,d_info in enumerate(DIRECT):
        if point_add(size, x, d_info) == y:
            return True
    return False

def get_direction(size, x, y):
    for d,d_info in enumerate(DIRECT):
        if point_add(size, x, d_info) == y:
            return d

def get_black_holes(map, info):
    black_holes = map['walls'][:]
    for i,snake in enumerate(info['snakes']):
        black_holes += snake['body']
    return set(black_holes)

def build_base_graph(map, info):
    '''
    将地图和障碍物数据变成图
    不考虑当前蛇是谁
    '''
    #snake = info['snakes'][seq]
    #head = snake['body'][0]
    #food_type = 'eggs' if snake['type'] == 'python' else 'gems'
    #nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'

    g = {}
    black_holes = get_black_holes(map, info)

    portals = map['portals']
    portals_map = {}
    for pindex in range(len(portals) /2):
        pin, pout = portals[pindex * 2], portals[pindex * 2 + 1]
        #如果传送门被死蛇占据了位置
        if pin in black_holes or pout in black_holes:
            if pin not in black_holes:
                black_holes.add(pin)
            if pout not in black_holes:
                black_holes.add(pout)
            continue
        portals_map[pin] = pout
        portals_map[pout] = pin

    w,h = map['size']
    nodes = set(itertools.product(range(w), range(h)))
    nodes = nodes - black_holes
    for snake in info['snakes']:
        if snake['alive']:
            head = snake['body'][0]
            nodes.add(head)

    for p in nodes:
        g[p] = {}
        for i in range(0, 4):
            np = point_add(map['size'], p, direction_delta[i])
            if np in nodes:
                g[p][np] = 1
    return g, nodes, portals_map

def apply_portals(g, portals_map, map):
    '''
        Before:
        A,B is portal pair
        A,C A,D A,E = 1
        B,X B,Y B,Z = 1
        After:
        A,Z A,Y A,Z = 2 
        B,C B,D B,E = 2
    '''
    for fnode, tnode in portals_map.items():
        if fnode not in g or tnode not in g:
            continue
            
        fl_nodes = g[fnode]
        tl_nodes = g[tnode]

        meta = g.get('portal_meta', {})

        for fn in fl_nodes:
            for tn in tl_nodes:
                if abs(get_direction(map['size'], fn, fnode)-get_direction(map['size'], tnode, tn)) != 2:
                    g[fn][tn] = g[fn][fnode] + g[tnode][tn]
                    g[tn][fn] = g[tn][tnode] + g[fnode][fn]
                    meta[(fn, tn)] = fnode
                    meta[(tn, fn)] = tnode
                
        for fn in fl_nodes:
            del g[fn][fnode]
        for tn in tl_nodes:
            del g[tn][tnode]
        del g[fnode]
        del g[tnode]

        g['portal_meta'] = meta

    return g
    
def remove_node(g, node):
    if node in g:
        for lnode in g[node]:
            del g[lnode][node]
        del g[node]
    return g

def change_distance(g, node, distance):
    if node in g:
        for lnode in g[node]:
            g[lnode][node] = distance
            g[node][lnode] = distance
    return g
        
def apply_noturn_back(g, head, size, direction):
    for node in g[head]:
        dir = get_direction(size, head, node)
        #go by portal
        if not dir:
            continue
        if abs(dir-direction) == 2:
            del g[head][node]
            del g[node][head]
            break

def build_per_snake_graph(map, info, seq, g, portals_map):
    g = copy.deepcopy(g)
    me = info['snakes'][seq]
    head = me['body'][0]
    food_type = 'eggs' if me['type'] == 'python' else 'gems'
    nonfood_type = 'gems' if me['type'] == 'python' else 'eggs'

    #remove other snake's head , as we can't go there
    for snake_seq,snake in enumerate(info['snakes']):
        if snake['alive'] and seq != snake_seq:
            remove_node(g, snake['body'][0])

    #apply non-food type distance 
    for node in info[nonfood_type]:
        change_distance(g, node, 999)

    apply_portals(g, portals_map, map)

    apply_noturn_back(g, head, map['size'], me['direction'])

    return g

def next_move_access_area(g, map, snake):
    if not snake['alive'] or snake['sprint'] < 0:
        return  {}
    area = {}
    head = snake['body'][0]
    for directon in range(0, 4):
        if abs(directon - snake['direction']) != 2:
            node = head
            for step in range(0, SPRINT_STEP):
                node = point_add(map['size'], node, DIRECT[directon])
                if node in g:
                    if snake['sprint'] == 0 and step == 0:
                        area[node] = 2
                    elif snake['sprint'] >0:
                        area[node] = 2
                    else:
                        area[node] = 1
    return area   

def access_length(g, node, can_not_go=[]):
    '''
    判断是否危险，如果可以接触到区域小于 limit ,则认为危险
    '''
    #thanks @http://eriol.iteye.com/blog/1171820
    queue = deque([node])
    dist = {}
    dist[node] = 0
    root = None
    while len(queue) > 0:
        root = queue.popleft()
        for nn in g[root]:
            if nn in can_not_go:
                continue
            if nn not in dist:
                dist[nn] = dist[root] + 1;  
                queue.append(nn)

    return dist.get(root, 0)

def make_decision(map, info, seq):
    '''
    根据当前的信息
    map
    info
    seq
    来做出决策
    '''

    g, nodes, portals_map = build_base_graph(map, info)
    snake_gs = {}
    danger_zone = {}
    for snake_seq,snake in enumerate(info['snakes']):
        if snake['alive']:
            snake_head = snake['body'][0]
            snake_g = build_per_snake_graph(map, info, snake_seq, g, portals_map)
            D,P = Dijkstra(snake_g, snake_head)
            snake_gs[snake_seq] = {
                'seq' : snake_seq,
                'head' : snake_head,
                'g' : snake_g,
                'D' : D,
                'P' : P
            }
            if snake_seq != seq:
                for n,df in next_move_access_area(snake_g, map, snake).items():
                    danger_zone[n] = danger_zone.get(n, 0) + df
    
    print 'danger', danger_zone
    #all data is ready 

    me = info['snakes'][seq]
    food_type = 'eggs' if me['type'] == 'python' else 'gems'
    nonfood_type = 'gems' if me['type'] == 'python' else 'eggs'

    #first step, how safe which directon is ?
    my_g = snake_gs[seq]['g']
    my_head = me['body'][0]
    rank = {}

    for nextnode in my_g[my_head]:
        al = access_length(my_g, nextnode, [my_head])
        rank[nextnode] = {
            'safe_next_move' : -danger_zone.get(nextnode, 0),
            'free_space' : al, 'safe' : al >= len(me['body']),
            'control_food' : 0, 'control_food_min_dis' : 999999,
            'access_food' : 0, 'access_food_min_dis' : 999999
        }
 
    #find nearest food , I can access / control
    access_food = {}
    access_food_count = 0
    control_food = {}
    control_food_count = 0

    for node in info[food_type]:
        reachable_snakes = []
        for snake_seq, sg in snake_gs.items():
            distance = sg['D'].get(node, None)
            if distance is not None:
                path = shortestPathFromDP(sg['D'], sg['P'], sg['head'], node)
                item = {'seq' : sg['seq'], 'distance' : distance, 'next' : path[1], 'path' : path}
                reachable_snakes.append(item)
                if sg['seq'] == seq:
                    #make sure I can reach there *before* other
                    item['distance'] += 0.5
                    access_food_count += 1
                    access_food[node] = item

        if len(reachable_snakes) > 0:
            dom = min(reachable_snakes, key=lambda x:x['distance'])
            if dom['seq'] == seq:
                control_food[node] = dom

    for food, meta in control_food.items():
        nextnode = meta['next']
        rank[nextnode]['control_food'] += 1
        if meta['distance'] < rank[nextnode]['control_food_min_dis']:
            rank[nextnode]['control_food_min_dis'] = meta['distance']

    for food, meta in access_food.items():
        nextnode = meta['next']
        rank[nextnode]['access_food'] += 1
        if meta['distance'] < rank[nextnode]['access_food_min_dis']:
            rank[nextnode]['access_food_min_dis'] = meta['distance']

    def key_func(choice):
        node, meta = choice
        key = None
        if meta['safe']:
            key =  (meta['safe_next_move'], meta['safe'], meta['control_food'] > 0, -meta['control_food_min_dis'], 
                    meta['access_food'] > 0, -meta['access_food_min_dis'], meta['free_space'])
        else:
            key =  (meta['safe_next_move'], meta['safe'], meta['free_space'], 0, 0, 0, 0)
        
        meta['_key'] = key
        return key

    for dir,row in rank.items():
        print dir, row 
    if len(rank) > 0:
        go = max(rank.items(), key=key_func)
        next = go[0]
        logging.info('go ' +  str(go))
        for d, d_info in enumerate(DIRECT):
            pos = point_add(map['size'], my_head, d_info)
            if pos == next:
                return d
            elif pos in portals_map:
                if my_g['portal_meta'].get((my_head, next)) == pos:
                    logging.info('go portal %s' %str(pos))
                    return d
                #pos = portals_map[pos]
                #if is_near(map['size'], pos, next):
                #    return d
        logging.error('fail to calculate dir')
    else:
        logging.warn("no way to go")
        return me['direction']

class Agent(Fnake):

    name = 'fnake-%d' % random.randint(0, 9999)
    type = 'python'
    #name = 'fnake'

    def make_decision(self):
        return make_decision(self.map, self.info, self.seq)

if __name__=="__main__":
    if sys.argv[1] == 'ws':
        ai = Agent()
        run_ai(ai, int(sys.argv[2]))
    else:
        cmd_run(Agent)

