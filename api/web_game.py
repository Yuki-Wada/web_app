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

class WebGameLogic:
    def __init__(self):
        import numpy as np
        self.deck = np.random.permutation(52)
        self.pos = 0
        self.session_ids = None
        self.has_initialized = False

    def get_next_card(self):        
        card_number = self.deck[self.pos]
        self.pos += 1
        return {
            'mark': int(card_number / 13) + 1,
            'number': int(card_number % 13 + 1)
        }

    def initialize_game(self, session_ids, sending_session_id):
        self.has_initialized = True
        self.pos = 0

        self.session_ids = list(session_ids)
        self.active_session_index = self.session_ids.index(sending_session_id)
    
        self.session_id_to_status = {}
        session_id_to_data = {}

        self.session_id_to_status['common'] = {
            'card_number': []
        }

        field_info = {}
        for session_id in self.session_ids:
            field_info[session_id] = {
                'money': 100,
                'bet': 0
            }

        for session_id in self.session_ids:
            self.session_id_to_status[session_id] = {
                'money': 100,
                'bet': 0,
                'card_number': []
            }
            session_id_to_data[session_id] = {
                'type': 'initialize_game',
                'common': {
                    'card': {
                        'type': 'add',
                        'number': []
                    }
                },
                'my_field': {
                    'card': {
                        'type': 'add',
                        'number': []
                    }
                },
                'field': field_info
            }
            if session_id == sending_session_id:
                session_id_to_data[session_id]['bet_now'] = True
            else:
                session_id_to_data[session_id]['bet_now'] = False

        for _ in range(3):
            card = self.get_next_card()
            self.session_id_to_status['common']['card_number'].append(card)
            for session_id in self.session_ids:
                session_id_to_data[session_id]['common']['card']['number'].append(card)

        for session_id in self.session_ids:
            for _ in range(2):
                card = self.get_next_card()
                self.session_id_to_status[session_id]['card_number'].append(card)
                session_id_to_data[session_id]['my_field']['card']['number'].append(card)
        
        return session_id_to_data
    
    def bet(self, amount, sending_session_id):
        self.session_id_to_status[sending_session_id]['money'] -= amount
        self.session_id_to_status[sending_session_id]['bet'] += amount

        self.increment_active_session()

        session_id_to_data = {}
        for session_id in self.session_ids:
            if self.is_active(session_id):
                session_id_to_data[session_id] = {
                    'type': 'bet',
                    'bet_now': True,
                    'bet_info': {
                        'bettor': sending_session_id,
                        'bet_amount': amount
                    }
                }
            else:
                session_id_to_data[session_id] = {
                    'type': 'bet',
                    'bet_now': False,
                    'bet_info': {
                        'bettor': sending_session_id,
                        'bet_amount': amount
                    }
                }

        return session_id_to_data

    def is_active(self, session_id):
        return self.session_ids[self.active_session_index] == session_id

    def normalize_active_session_index(self):
        self.active_session_index %= len(self.session_ids)

    def increment_active_session(self):
        self.active_session_index += 1
        self.normalize_active_session_index()

class WebGame:
    def __init__(self):
        self.session_id_to_web_sockets = {}
        self.session_id_to_web_socket_count = {}

        self.session_order = []
        self.active_session_index = -1

        self.logic = WebGameLogic()
        
    def set_web_socket(self, web_socket, session_id):
        if session_id not in self.session_id_to_web_socket_count:
            self.session_id_to_web_sockets[session_id] = []
            self.session_id_to_web_socket_count[session_id] = 0
            self.session_order.append(session_id)
        self.session_id_to_web_sockets[session_id].append(web_socket)
        self.session_id_to_web_socket_count[session_id] += 1

        if self.active_session_index == -1:
            self.active_session_index = 0

    def send_data(self, session_id_to_data):
        for session_id in session_id_to_data:
            if session_id not in self.session_id_to_web_socket_count:
                del self.session_id_to_web_sockets[session_id]
                continue
            web_sockets = self.session_id_to_web_sockets[session_id]
            data = session_id_to_data[session_id]
            print(data)
            for i, web_socket in enumerate(web_sockets):
                if web_socket.closed:
                    del self.session_id_to_web_sockets[session_id][i]
                    continue
                web_socket.send(json.dumps(data))

    def get_message(self, message, sending_session_id):
        if message['type'] == 'initialize_page':
            session_id_to_data = {}
            for session_id in self.session_id_to_web_sockets:
                session_id_to_data[session_id] = {
                    'type': 'initialize_page',
                    'input_message': False,
                    'participant_count': self.participant_count,
                }
            self.send_data(session_id_to_data)
        elif message['type'] == 'initialize_game':
            session_id_to_data = self.logic.initialize_game(
                self.session_id_to_web_sockets.keys(), sending_session_id)
            self.send_data(session_id_to_data)
        elif message['type'] == 'bet':
            session_id_to_data = self.logic.bet(
                message['amount'], sending_session_id)
            self.send_data(session_id_to_data)

    def close_web_socket(self, session_id):
        self.session_id_to_web_socket_count[session_id] -= 1
        if self.session_id_to_web_socket_count[session_id] == 0:
            del self.session_id_to_web_socket_count[session_id]
        
    def assign_session_id(self):
        import random
        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        while True:
            session_id = ''.join(random.choices(letters, k=20))
            if session_id not in self.session_id_to_web_socket_count:
                break
        return session_id

    @property
    def participant_count(self):
        return len(self.session_id_to_web_socket_count)

app.game = WebGame()
@app.route('/test')
def test():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        chat_id = session.get('chat_id')
        app.game.set_web_socket(ws, chat_id)
        while True:
            time.sleep(1/ 60)
            message = ws.receive()

            # Web Socket 破棄時の処理
            if message is None:
                app.game.close_web_socket(chat_id)
                break

            # メッセージ取得時の処理
            message = json.loads(message)
            app.game.get_message(message, chat_id)

    return ''

@app.route('/session')
def get_session():
    return session['chat_id']
