#!/usr/bin/env python
#coding=utf-8
import logging
import httplib
import urllib
import json
import time
import random

from ailib import BaseAI,SPRIT_COMMAND
NEED_ADDING, RUNNING = 0, 1

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


class WebSocketController():
    """
    提供给ai操作的websocket接口
    """
    def __init__(self, room):
        self.ws = None
        self.room = room
        self.me = None

    def cmd(self, cmd, data={}):
        """
        发送命令给服务器
        """
        if not self.ws:
            logging.debug('ws not connected')
            return 
                
        data['op'] = cmd
        data['room'] = self.room
        self.ws.send(json.dumps(data))
        # logging.debug('post: %s : %s', cmd, data)

    def add(self, name, type):
        self.cmd("add",
                           dict(name = name,
                                type = type))
    
    def map(self):
        self.cmd("map")

    def info(self):
        self.cmd("info")

    def sprit(self):
        self.cmd("sprit")
        
    def turn(self, dir):
        self.cmd("turn",
                 dict(id = self.me["id"],
                      round = -1,
                      direction = dir))

    def sub_info(self):
        time.sleep(0.3)
        self.info()



import websocket
#websocket.enableTrace(True)

def run_ai(ai, room):
    addr = 'game.snakechallenge.org:9999/info'

    controller = WebSocketController(room=room)

    def on_open(ws):
        logging.debug('ws opened')
        controller.ws = ws
        controller.cmd('setroom', {'room' : room})
        controller.add(ai.name, ai.type)
        controller.map()
        controller.info()
        
    def on_message(ws, data):
        data = json.loads(data)
        op = data.get('op', None)
        logging.debug('on_message op=%s' %op)
        if op == 'info':
            names = [s['name'] for s in data['snakes']]
            if ai.name in names:
                me = data['snakes'][names.index(ai.name)]
            else:
                me = None
            if ai.status == NEED_ADDING:
                # if already added, not add again
                if me:
                    return
                else:
                    controller.add(ai.name, ai.type)
            elif ai.status == RUNNING:
                if not me: return 

                # 如果自己死掉了, 那就不发出操作
                if not me['alive']:
                    logging.debug(ai.name+' is dead.')
                    ai.status = NEED_ADDING            
                else:
                    step = ai.step(data)
                    if step == SPRIT_COMMAND:
                        controller.sprit()
                    else:
                        controller.turn(step)
        elif op == 'add':
            controller.me = data
            ai.seq = data['seq']
            ai.id = data['id']
            ai.status = RUNNING
        elif op == 'map':
            ai.setmap(data)
        elif data['status'] != 'ok':
            logging.error(data)

    def on_error(ws, exc):
        logging.error(exc)

    def on_close(ws):
        logging.error('ws closed')

    ws = websocket.WebSocketApp("ws://" + addr,
            on_open = on_open,
            on_message = on_message,
            on_error = on_error,
            on_close = on_close)
    ws.run_forever()
