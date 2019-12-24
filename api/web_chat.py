import json
import datetime
import time
import pandas as pd
import sqlite3

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'hoge'
CORS(app)

class WebChatLogic:
    def __init__(self):
        pass

    def get_result(self, input_message):
        datetime_now = datetime.datetime.now()
        data = {
            'input_message': True,
            'message': input_message,
            'time': str(datetime_now),
        }
        return data

class WebChat:
    def __init__(self):
        self.session_id_to_web_sockets = {}
        self.session_id_to_web_socket_count = {}

        self.session_order = []
        self.active_session_index = -1

        self.logic = WebChatLogic()
        
    def set_web_socket(self, web_socket, session_id):
        if session_id not in self.session_id_to_web_socket_count:
            self.session_id_to_web_sockets[session_id] = []
            self.session_id_to_web_socket_count[session_id] = 0
            self.session_order.append(session_id)
        self.session_id_to_web_sockets[session_id].append(web_socket)
        self.session_id_to_web_socket_count[session_id] += 1

        if self.active_session_index == -1:
            self.active_session_index = 0

    def send_data(self, data):
        for session_id, web_sockets in list(self.session_id_to_web_sockets.items()):
            if session_id not in self.session_id_to_web_socket_count:
                del self.session_id_to_web_sockets[session_id]
                continue
            for i, web_socket in enumerate(web_sockets):
                if web_socket.closed:
                    del self.session_id_to_web_sockets[session_id][i]
                    continue
                data['is_active'] = app.game.is_active(session_id)
                web_socket.send(json.dumps(data))
        print(data)

    def get_message(self, message, session_id):
        if message['type'] == 'initialize':
            data = {
                'input_message': False,
                'participant_count': self.participant_count,
            }
        elif message['type'] == 'input_message':
            data = self.logic.get_result(message['message'])
            data['participant_count'] = self.participant_count
            data['chat_id'] = str(session_id)
            self.increment_active_session()

        print(message)
        self.send_data(data)

    def close_web_socket(self, session_id):
        self.session_id_to_web_socket_count[session_id] -= 1
        if self.session_id_to_web_socket_count[session_id] == 0:
            del self.session_id_to_web_socket_count[session_id]

        for i, check_id in enumerate(self.session_order):
            if check_id == session_id:
                break
        del self.session_order[i]
        if self.active_session_index > i:
            self.active_session_index -= 1
        self.normalize_active_session_index()

        data = {
            'input_message': False,
            'participant_count': app.game.participant_count,
        }
        self.send_data(data)

    def is_active(self, session_id):
        return self.active_session == session_id

    def normalize_active_session_index(self):
        if len(self.session_order) == 0:
            self.active_session_index = -1
        elif self.active_session_index >= len(self.session_order):
            self.active_session_index %= len(self.session_order)

    def increment_active_session(self):
        self.active_session_index += 1
        self.normalize_active_session_index()
        
    def assign_session_id(self):
        import random
        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        while True:
            session_id = ''.join(random.choices(letters, k=20))
            if session_id not in self.session_id_to_web_socket_count:
                break
        return session_id

    @property
    def active_session(self):
        return self.session_order[self.active_session_index]

    @property
    def participant_count(self):
        return len(self.session_id_to_web_socket_count)

app.chat = WebChat()
@app.route('/pipe')
def pipe():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        chat_id = session.get('chat_id')
        app.chat.set_web_socket(ws, chat_id)
        while True:
            time.sleep(1/ 60)
            message = ws.receive()

            # Web Socket 破棄時の処理
            if message is None:
                app.game.close_web_socket(chat_id)
                break

            # メッセージ取得時の処理
            message = json.loads(message)
            app.chat.get_message(message, chat_id)

    return ''
