#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function
import logging
import httplib
import urllib
import json
import time
import random

from ailib import BaseAI

class Fnake(BaseAI):

    name = 'fnake'
    type = 'python'

    def setmap(self, gmap):
        gmap['walls'] = map(tuple, gmap['walls'])
        gmap['portals'] = map(tuple, gmap['portals'])
        self.map = gmap

    def step(self, info):
        info['eggs'] = map(tuple, info['eggs'])
        info['gems'] = map(tuple, info['gems'])
        for snake in info['snakes']:
            snake['body'] = map(tuple, snake['body'])
        self.info = info

        self.log('thinking .... ')
        command = self.make_decision()
        self.log('go %s ' %command)
        return command
 
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
        logging.debug("[%s-%s]" + " %s" * len(msg), self.name, self.type, *msg)
