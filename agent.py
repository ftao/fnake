#!/usr/bin/env python
#coding=utf8
from fnake import Fnake
import random
import time
from dijkstra import shortestPath,Dijkstra
import copy 
import itertools

def point_add(size, x, y):
    return [(x[0] + y[0]) % size[0], (x[1] + y[1]) % size[1]]


class Agent(Fnake):

    name = 'fnake-%d' % random.randint(0, 9999)

    direction_delta = [
        [-1, 0],
        [0, -1],
        [1, 0],
        [0, 1],
    ]

    def make_decision(self):
        '''
        根据当前的信息
        map
        info
        来做出决策
        '''

        current_direction = self.info['snakes'][self.me['seq']]['direction']

        #不能往回走
        choices = [(i, self.rank(i)) for i in range(0,4) if (current_direction + 2) %4 != i]

        self.log('ranks', choices)
        max_v = max(choices, key = lambda x:x[1])[1]
        choices = [item for item in choices if item[1] == max_v]
        self.log('mav-choices', choices)
        go = choices[random.randint(0, len(choices) -1)]
        self.log('go', go)
        return go[0]

    
    def move(self, map, info, snake_seq, move):
        '''
        移动某一条蛇之后新世界
        '''
        info = copy.deepcopy(info)
        snake = info['snakes'][snake_seq]
        point = point_add(map['size'], snake['body'][0], self.direction_delta[move])

        assert point not in map['walls']
        for s in info['snakes']:
            assert point not in s['body']
 
        snake['body'].pop()
        snake['body'].insert(0, point)
        return info

    def near_food_dis(self):
        map = self.map
        info = self.info
        snake_seq =  self.me['seq']
        snake = info['snakes'][snake_seq]
        head = snake['body'][0]

        food_type = 'eggs' if snake['type'] == 'python' else 'gems'

        g = self.build_graph(map, info, snake_seq)
        D,P = Dijkstra(g, tuple(head))
        return min([D.get(tuple(p), 99999) for p in info[food_type]])


    def rank(self, move):
        '''
        在执行*move 之后的评分
        怎么评分:
        1. 如果死了 -128
        1. 如果没死，但是短了 -64
        1. 如果没死，没短
           a. 1000 - 到最近食物的距离
           #a. 控制区域大小 - This One
           #a. 如果吃到食物
           #a. 控制区域内食物数目
           #a. 控制区域内毒药数目
           #a. 距离食物的距离  - 总共的，还是就最近的?
        '''
        map = self.map
        info = self.info
        snake_seq =  self.me['seq']
        snake = info['snakes'][snake_seq]

        try:
            ninfo = self.move(map, info, snake_seq, move)
        except AssertionError,e:
            print e
            self.log('illegal move ', move)
            return -128

        score = self.score(map, ninfo, snake_seq)

        food_type = 'eggs' if snake['type'] == 'python' else 'gems'
        nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'


        if score > -128:
        #if True
            #body_score = self.open_space([newhead] + self.myself['body'][:-1])
            #the new world

            #build the graphy
            snake_count = len(ninfo['snakes'])
            dis = [({},{})] * snake_count
            for i in range(0, snake_count):
                #只考虑同类
                if ninfo['snakes'][i]['alive'] and ninfo['snakes'][i]['type'] == info['snakes'][snake_seq]['type']:
                    head = ninfo['snakes'][i]['body'][0]
                    g = self.build_graph(map, ninfo, i)
                    D,P = Dijkstra(g, tuple(head))
                    dis[i] = (D,P)

            control_area = 0
            food_score = 0

            #food control score
            #food_dis
            food_ds = {}
            '''
            for (i,j) in itertools.product(range(map['size'][0]), range(map['size'][1])):
                ds = [(k, dis[k][0].get((i,j), 999999+(k-snake_seq)%snake_count)) for k in range(snake_count)]
                #控制这个点的蛇
                dom = min(ds, key = lambda x:x[1])
                #如果是我
                if dom[0] == snake_seq:
                    #control_area += 1
                    #如果是食物
                    if [i,j] in ninfo[food_type]:
                        self.log('near food', [i,j], dom[1])
                        #food_score += 1
                        food_ds[(i,j)] = dom[1]
            '''

            #找到我能控制的食物及其距离
            for [i,j] in ninfo[food_type]:
                ds = [(k, dis[k][0].get((i,j))) for k in range(snake_count) if (i,j) in dis[k][0]]
                if len(ds) > 0:
                    dom = min(ds, key = lambda x:x[1])
                    if dom[0] == snake_seq:
                        self.log('near food', [i,j], dom[1])
                        #food_score += 1
                        food_ds[(i,j)] = dom[1]

            nf_score = 0
            if len(food_ds) > 0:
                self.log('food_dis', food_ds)
                nf_score = 99999 - min(food_ds.values())            

            #nearlist foood 
            #

            control_score =  control_area

            #self.near_food, self.food_should_go = self.find_near_food()
            #self.log('near_food', self.near_food)
 
            #self.log('body_socre', body_score)
            #print newhead, self.food_should_go
            #if newhead == self.food_should_go:
            #    food_score = 64
            #else:
            #    food_score = 16
            #food_score = self.food_score(newhead)
            self.log('move,score,control_score,food_score,nf_score', move,score, control_score, food_score, nf_score)
            return score + control_score + food_score + nf_score
        else:
            self.log('it will die ', move, score)
            #这个操作会导致死亡
            return score


    def score(self, map, info, snake_seq):
        '''
        基本的打分, 如果死了返回-128
        如果吃到非食物返回 0 - -127
        如果吃到食物返回 128
        否则返回0
        '''

        snake = info['snakes'][snake_seq]
        food_type = 'eggs' if snake['type'] == 'python' else 'gems'
        nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'

        head = snake['body'][0]

        if head in map['walls']:
            #碰到墙
            return -128

        for i,snake in enumerate(info['snakes']):
            if i == snake_seq:
                #碰到自己
                if head in snake['body'][1:]:
                    return -128
            else:
                #碰到别人
                if head in snake['body']:
                    return -128

        if head in info[nonfood_type]:
            #吃到非食物导致死亡
            return -128 + len(snake['body']) - 5

        if head in info[food_type]:
            return 128 

        return 0

    def _myself(self):
        return self.info['snakes'][self.me['seq']]

    myself = property(_myself)

    def open_space(self, body):
        score = 0
        for point in body:
            for i in range(0, 4):
                if self.score(self.point_add(point, self.direction_delta[i])) >= 0:
                    score += 1
        return score                
                    
    def shortest_path(self, g, pa, pb):
        '''
        从pa 到 pb 需要的步数和下一步应该去的地方
        '''
        pa = tuple(pa)
        pb = tuple(pb)
        try:
            path = shortestPath(g, pa, pb)
            #self.log('===========path',  path)
            return [len(path), list(path[1])]
        except Exception,e:
            self.log('.....exception',  e)
            return [99999, None]

    def find_near_food(self, newhead):
        '''最近的食物
        food_point, length, newpoint
        '''
        g = self.build_graph(newhead)
        self.log('------newhead is ', newhead)
        dis = [[point] + self.shortest_path(g, head, point)  for point in self.info[FOOD]]
        if len(dis) > 0:
            near_food = min(dis, key = lambda x:x[1])
            return near_food
        else:
            return None,None,None

    def build_graph(self, map, info, snake_seq):
        '''
        将地图和障碍物数据变成图
        '''
        snake = info['snakes'][snake_seq]
        food_type = 'eggs' if snake['type'] == 'python' else 'gems'
        nonfood_type = 'gems' if snake['type'] == 'python' else 'eggs'

        g = {}

        black_holes = map['walls'][:]
        head = info['snakes'][snake_seq]['body'][0]

        for i,snake in enumerate(info['snakes']):
            if i == snake_seq:
                black_holes += snake['body'][1:]
            else:
                black_holes += snake['body']

        #ignore non-food 
        #if len(snake['body']) <= 5:
        #    black_holes += info[nonfood_type]

        for x in range(map['size'][0]):
            for y in range(map['size'][1]):
                p = [x,y]
                if p not in black_holes:
                    g[tuple(p)] = {}
                    for i in range(0, 4):
                        np = point_add(map['size'], p, self.direction_delta[i])
                        if np not in black_holes:
                            if np in info[nonfood_type]:
                                g[tuple(p)][tuple(np)] = 999
                            else:
                                g[tuple(p)][tuple(np)] = 1
                        
        return g
        #self.log(g)

        
def main(type):
    agent = Agent()
    agent.type = type
    agent.cmd_map()
    agent.log(agent.map['size'])
    agent.cmd_add()
    while True:
        time.sleep(0.2)
        agent.log('start new turn')
        agent.cmd_turn()
        agent.log('end turn')
    
if __name__=="__main__":
    import sys
    if len(sys.argv) > 1:
        type = sys.argv[1]
    else:
        type = 'pyton'
    main(type)

