#!/usr/bin/env python
#coding=utf8
from fnake import Fnake
import random
import time
from dijkstra import shortestPath

FOOD = 'eggs'
POISON = 'gems'

class Agent(Fnake):

    name = 'fnake-%d' % random.randint(0, 9999)

    direction_delta = {
        0 : [-1, 0],
        1 : [0, -1],
        2 : [1, 0],
        3 : [0, 1],
    }

    def make_decision(self):
        '''
        根据当前的信息
        map
        info
        来做出决策
        '''

        self.near_food, self.food_should_go = self.find_near_food()

        self.log('near_food', self.near_food)
        choices = [(i, self.vote(self.point_add(self.myself['body'][0], self.direction_delta[i])))
                   for i in range(0,4)]
        self.log('vote', choices)
        max_v = max(choices, key = lambda x:x[1])[1]
        choices = [item for item in choices if item[1] == max_v]
        go = choices[random.randint(0, len(choices) -1)]
        self.log('go', go)
        return go[0]


    def vote(self, newhead):
        score = self.score(newhead)
        if score > -128:
            body_score = self.open_space([newhead] + self.myself['body'][:-1])
            self.log('body_socre', body_score)
            print newhead, self.food_should_go
            if newhead == self.food_should_go:
                food_score = 64
            else:
                food_score = 16
            #food_score = self.food_score(newhead)
            self.log('food_score', food_score)
            return score + body_score + food_score
        else:
            return score


    def score(self, point):

        if point in self.map['walls']:
            return -128

        for snake in self.info['snakes']:
            if point in snake['body']:
                return -128

        for snake in self.info['snakes']:
            if point in snake['body']:
                return -128

        if point in self.info[POISON]:
            return -128 + len(self.myself['body']) - 5

        if point in self.info[FOOD]:
            return 128 

        return 0

    def _myself(self):
        return self.info['snakes'][self.me['seq']]

    myself = property(_myself)

    def point_add(self, x, y):
        return [(x[0] + y[0]) % self.map['size'][0], (x[1] + y[1]) % self.map['size'][1]]

    def open_space(self, body):
        score = 0
        for point in body:
            for i in range(0, 4):
                if self.score(self.point_add(point, self.direction_delta[i])) >= 0:
                    score += 1
        return score                
                    
    def shortest_path(self, pa, pb):
        '''
        从pa 到 pb 需要的步数和下一步应该去的地方
        '''
        pa = tuple(pa)
        pb = tuple(pb)
        try:
            path = shortestPath(self.graphy, pa, pb)
            self.log('===========path',  path)
            return [len(path), list(path[1])]
        except Exception,e:
            self.log('.....exception',  e)
            return [99999, None]

    def find_near_food(self):
        '''最近的食物'''
        head = self.myself['body'][0]
        self.log('------head is ', self.myself['body'][0])
        dis = [[point] + self.shortest_path(head, point)  for point in self.info[FOOD]]
        self.log('dis.....', dis)
        if len(dis) > 0:
            near_food = min(dis, key = lambda x:x[1])
            return near_food[0],near_food[2]
        else:
            return None,None

    def build_graph(self):
        '''
        将地图和障碍物数据变成图
        '''
        g = {}
        points = []

        black_holes = self.map['walls']
        for i,snake in enumerate(self.info['snakes']):
            if i == self.me['seq']:
                black_holes += snake['body'][1:]
            else:
                black_holes += snake['body']

        if len(self.myself['body']) <= 5:
            black_holes += self.info[POISON]

        for x in range(self.map['size'][0]):
            for y in range(self.map['size'][1]):
                p = [x,y]
                if p not in black_holes:
                    g[tuple(p)] = {}
                    for i in range(0, 4):
                        np = self.point_add(p, self.direction_delta[i])
                        if np not in black_holes:
                            g[tuple(p)][tuple(np)] = 1
        self.graphy = g
        #self.log(g)

def main(type):
    agent = Agent()
    agent.type = type
    agent.cmd_map()
    agent.log(agent.map['size'])
    agent.cmd_add()
    agent.build_graph()
    while True:
        time.sleep(0.2)
        agent.log('start new turn')
        agent.cmd_turn()
        agent.build_graph()
        agent.log('end turn')
    
if __name__=="__main__":
    import sys
    if len(sys.argv) > 1:
        type = sys.argv[1]
    else:
        type = 'pyton'
    print('type', type)
    if type == 'ruby':
        FOOD = 'gems'
        POISON = 'eggs'
    else:
        FOOD = 'eggs'
        POISON = 'gems'
    main(type)

