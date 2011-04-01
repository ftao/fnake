#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import httplib
import urllib
import json
import time
import random

class Fnake(object):

    name = 'fnake'
    type = 'python'

    def __init__(self):
        self.conn = httplib.HTTPConnection("pythonvsruby.org")#"localhost:4567")

    def post(self, cmd, data):
        """
        发送命令给服务器
        """
        self.conn.request("POST", '/room/1/%s' % cmd,
                          urllib.urlencode(data))
        result = self.conn.getresponse().read()
#        self.log(result)
        return json.loads(result)

    def get(self, cmd):
        """
        获取信息
        """
        self.conn.request("GET", '/room/1/%s' % cmd)
        result = self.conn.getresponse().read()
        return json.loads(result)
    
    def cmd_add(self):
        """
        添加新的蛇
        """
        result = self.post("add",
                           dict(name = self.name,
                                type = self.type))
        self.me, self.info = result[0], result[1]
#        self.log(self.info)
        return self.me, self.info
    
    def cmd_turn(self):
        """
        控制蛇方向
        """
        current_direction = self.info["snakes"]\
                            [self.me["seq"]]\
                            ["direction"]
        self.log("current direction: %s" % current_direction)
      
        result = self.post("turn",
                           dict(id = self.me["id"],
                                round = self.info["round"],
                                direction = self.make_decision()))
        self.turn, self.info = result[0], result[1]

    def cmd_map(self):
        """
        获取地图信息
        """
        self.map = self.get("map")

    def cmd_info(self):
        """
        获取实时场景信息
        """
        self.info = self.get("info")


    def make_decision(self):
        '''
        根据当前的信息
        map
        info
        me
        来做出决策
        '''
        raise NotImplemented

    def log(self, *msg):
        print ('[%s-%s][%d]:'% (self.type, self.name, time.time()), *msg)

def main():
    fn = Fnake()
    while True:
        time.sleep(0.2)
        fn.cmd_turn()
    
if __name__=="__main__":
    main()
