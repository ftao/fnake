#!/usr/bin/env python
#coding=utf8
from fnake import Fnake
import random
import time
from dijkstra import shortestPath,Dijkstra
import copy 
import itertools

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

def get_black_holes(map, info, seq):
    black_holes = map['walls'][:]
    for i,snake in enumerate(info['snakes']):
        if i == seq:
            black_holes += snake['body'][1:]
        else:
            black_holes += snake['body']

            #for safety, add other snake's next pos to blackhole
            p = snake['body'][0]
            black_holes += [point_add(map['size'], p, direction_delta[i]) for i in range(4)]
    return black_holes

def build_graph(map, info, seq):
    '''
    将地图和障碍物数据变成图
    '''
    snake = info['snakes'][seq]
    head = snake['body'][0]
    food_type = 'eggs' if snake['type'] == 'python' else 'gems'
    nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'

    g = {}
    black_holes = get_black_holes(map, info, seq)

    portals = map['portals']
    portals_map = {}
    for pindex in range(len(portals) /2):
        pin, pout = portals[pindex * 2], portals[pindex * 2 + 1]
        portals_map[pin] = pout
        portals_map[pout] = pin
 
    head = info['snakes'][seq]['body'][0]

    w,h = map['size']
    nodes = [node for node in itertools.product(range(w), range(h)) if node not in black_holes]
    if head not in nodes:
        nodes.append(head)
    for p in nodes:
        g[p] = {}
        for i in range(0, 4):
            np = point_add(map['size'], p, direction_delta[i])
            if np not in nodes:
                continue
            np = portals_map.get(np, np)
            if np not in nodes:
                continue
            g[p][np] = 999 if np in info[nonfood_type] else 1

    return g

def make_decision(map, info, seq):
    '''
    根据当前的信息
    map
    info
    seq
    来做出决策
    '''

    current_direction = info['snakes'][seq]['direction']

    max_v = (-9999, 0, 0, 0, 0)
    max_command = current_direction
    for command in range(0,4):
        v = rank(map, info, seq, command)
        if v > max_v:
            max_v = v
            max_command = command
    print max_command, max_v
    return max_command

def rank(map, info, seq, command):
    '''
    '''
    seq =  seq
    me = info['snakes'][seq]

    score = 0
    try:
        ninfo = move(map, info, seq, command)
        score = base_score(map, ninfo, seq)
    except AssertionError,e:
        score = -128

    food_type = 'eggs' if me['type'] == 'python' else 'gems'
    nonfood_type = 'gems' if me['type'] == 'python' else 'eggs'

    if score > -128:
        snake_count = len(ninfo['snakes'])
        dis = []
        #for every snake , run Dijkstra algo
        for i, snake in enumerate(ninfo['snakes']):
            #只考虑同类
            #if ninfo['snakes'][i]['alive'] and ninfo['snakes'][i]['type'] == info['snakes'][seq]['type']:
            head = snake['body'][0]
            g = build_graph(map, ninfo, i)
            D,P = Dijkstra(g, head)
            dis.append({
                'seq' : i,
                'd_p' : (D,P)
            })

        access_area = 0
        access_food_count = 0
        access_food = {}

        control_area = 0
        control_food_count = 0
        control_food = {}

        w,h = map['size']

        def distance_key_func(x):
            if x['seq'] == seq:
                return x['distance'] + 2
            else:
                return x['distance']

        for point in itertools.product(range(w), range(h)):
            reachable_snakes = []
            for dis_item in dis:
                distance = dis_item['d_p'][0].get(point)
                if distance is not None:
                    reachable_snakes.append({'seq' : dis_item['seq'], 'distance' : distance})
            if len(reachable_snakes) > 0:
                for item in reachable_snakes:
                    if seq == item['seq']:
                        access_area += 1
                        if point in ninfo[food_type]:
                            access_food_count += 1
                            access_food[point] = item['distance']
                        break

                #控制这个点的蛇
                dom = min(reachable_snakes, key=distance_key_func)
                #如果是我
                if dom['seq'] == seq:
                    control_area += 1
                    #如果该点是食物
                    if point in ninfo[food_type]:
                        control_food_count += 1
                        control_food[point] = dom['distance']

        cf_score = 0
        if len(control_food) > 0:
            cf_score = 1000 - min(control_food.values())            

        af_score = 0
        if len(access_food) > 0:
            af_score = 1000 - min(access_food.values()) 

        #如果执行这一步会导致可接触区域小于我的长度，很危险!!!!
        if access_area <= len(snake['body']):
            return score, -64, cf_score, af_score, control_area
        else:
            return score, 0, cf_score, af_score, control_area
    else:
        #这个操作会导致死亡
        return score, 0, 0, 0, 0

def move(map, info, seq, command):
    '''
    移动某一条蛇之后新世界
    '''
    info = copy.deepcopy(info)
    snake = info['snakes'][seq]
    point = point_add(map['size'], snake['body'][0], direction_delta[command])

    assert point not in get_black_holes(map, info, seq)

    snake['body'].pop()
    snake['body'].insert(0, point)
    return info

def base_score(map, info, seq):
    '''
    基本的打分, 如果死了返回-128
    如果吃到非食物返回 -127 - 0
    如果吃到食物返回 128
    否则返回0
    '''

    snake = info['snakes'][seq]
    food_type = 'eggs' if snake['type'] == 'python' else 'gems'
    nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'

    head = snake['body'][0]

    if head in info[nonfood_type]:
        #吃到非食物
        return -128 + len(snake['body']) - 5
    elif head in info[food_type]:
        return 128 
    else:
        return 0

class Agent(Fnake):

    #name = 'fnake-%d' % random.randint(0, 9999)
    name = 'fnake'

    def make_decision(self):
        return make_decision(self.map, self.info, self.seq)

if __name__=="__main__":
    cmd_run(Agent)

