import json
import sqlite3
import pandas as pd
from flask import request, jsonify

"""
Train a maze task.
"""

import os
import argparse
import logging
from itertools import product
import random
from queue import Queue
import numpy as np

from api.models.reversi_env import ReversiEnv
from api.models.mcts import RandomPolicy, MCTS

class ReversiGame:
    def __init__(self, time_limit=3):
        self.env = ReversiEnv(
            player_color='black',
            opponent='random',
            observation_type='numpy3c',
            illegal_place_mode='lose',
            board_size=8,
        )
        self.observation = self.env.reset()
        self.policy = MCTS(time_limit=time_limit)
        self.stone = 0

    def get_state(self):
        return {
            'board': (self.observation[0] + self.observation[1] * 2).tolist(),
            'black': self.observation[0].sum(),
            'white': self.observation[1].sum(),
        }

    def should_skip_turn(self):
        possible_actions = self.env.get_possible_actions(self.env.state, self.stone)
        return 65 in possible_actions

    def switch_turn(self):
        self.stone = 1 - self.stone

    def can_place_stone(self, place_stone):
        player_action = place_stone[0] * 8 + place_stone[1]
        possible_actions = self.env.get_possible_actions(self.env.state, self.stone)
        return player_action in possible_actions

    def player_turn(self, place_stone):
        player_action = place_stone[0] * 8 + place_stone[1]
        self.policy.update_with_move(player_action)
        self.observation, _, done, _ = self.env.step(player_action, self.stone)
        self.stone = 1 - self.stone

        return self.get_state(), done

    def cpu_turn(self):
        cpu_action = self.policy.get_move(self.observation, self.env, self.stone)
        self.policy.update_with_move(cpu_action)
        self.observation, _, done, _ = self.env.step(cpu_action, self.stone)
        self.stone = 1 - self.stone

        return self.get_state(), done
