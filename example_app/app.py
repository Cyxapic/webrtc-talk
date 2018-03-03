#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import uuid

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler

from settings import IP, PORT


rel = lambda *x: os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

global_rooms = {}

logging.basicConfig(level=logging.DEBUG)

class Room(object):
    def __init__(self, name, video, clients=[]):
        self.name = name
        self.clients = clients

    def __repr__(self):
        return self.name


class MainHandler(RequestHandler):
    def get(self):
        self.render('index.html')


class RoomGenerateHandler(RequestHandler):
    def get(self, video):
        room = uuid.uuid4().hex.upper()[0:6]
        self.redirect(f'/room/{room}/{video}')


class RoomHandler(RequestHandler):
    def get(self, slug, video):
        self.render('room.html')


class EchoWebSocket(WebSocketHandler):
    def open(self, slug, video):
        if slug in global_rooms:
            global_rooms[slug].clients.append(self)
        else:
            global_rooms[slug] = Room(slug, video, [self])
        self.room = global_rooms[slug]
        if len(self.room.clients) > 2:
            self.write_message('fullhouse')
        elif len(self.room.clients) == 1:
            self.write_message('initiator')
        else:
            self.write_message('not initiator')
        logging.info(
            'WebSocket connection opened from %s', self.request.remote_ip)

    def on_message(self, message):
        logging.info(
            'Received message from %s: %s', self.request.remote_ip, message)
        for client in self.room.clients:
            if client is self:
                continue
            client.write_message(message)

    def on_close(self):
        logging.info('WebSocket connection closed.')
        self.room.clients.remove(self)


def main():
    settings = dict(
        template_path=rel('templates'),
        static_path=rel('static'),
        debug=True
    )

    application = Application([
        (r'/', MainHandler),
        (r'/enter-room/([^/]*)', RoomGenerateHandler),
        (r'/room/([^/]*)/([^/]*)', RoomHandler),
        (r'/ws/([^/]*)/([^/]*)', EchoWebSocket),
    ], **settings)

    application.listen(address=IP, port=PORT)
    logging.info(f"Started listening at {IP}:{PORT}.")
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
