#!/usr/bin/env python
#coding=utf8
from fnake import Fnake
import random
import time

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
            return score + body_score
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
                    
def main():
    agent = Agent()
    agent.cmd_map()
    agent.cmd_add()
    while True:
        time.sleep(0.2)
        agent.cmd_turn()
    
if __name__=="__main__":
    main()


