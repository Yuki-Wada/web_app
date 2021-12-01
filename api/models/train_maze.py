import random
import numpy as np
from flask import url_for


def get_default_maze_text():
    from api import app
    import os
    default_maze_path = os.path.join(app.static_folder, 'maze.txt')

    with open(default_maze_path, 'r') as f:
        maze_text = f.read()
    return maze_text


class MazeEnvironment:
    def __init__(self, maze_text=None):
        if maze_text is None:
            maze_text = get_default_maze_text()

        self.row = 0
        self.col = 0
        self.lines = []
        for line in maze_text.splitlines():
            line = line.strip()
            self.lines.append(line)
            self.col = max(self.col, len(line))
            self.row += 1

        self.maze = np.zeros((self.row, self.col), dtype=np.uint8)
        self.start = None
        self.goal = None
        for i, line in enumerate(self.lines):
            for j, ch in enumerate(line):
                if ch == '#':
                    self.maze[i, j] = 1
                elif ch == 'S':
                    if self.start is not None:
                        raise ValueError(
                            'It is not permitted that multiple starts exist.')
                    self.start = (i, j)
                elif ch == 'G':
                    if self.goal is not None:
                        raise ValueError(
                            'It is not permitted that multiple goals exist.')
                    self.goal = (i, j)

        if self.start is None:
            raise ValueError('It is not permitted that no start exists.')
        if self.goal is None:
            raise ValueError('It is not permitted that no goal exists.')

        self.state = self.start

    def reset(self):
        self.state = self.start
        return self.state

    def locate(self, state):
        if self.maze[tuple(state)] == 1:
            raise ValueError('The agent cannot live in a wall.')
        self.state = state

    def step(self, direction):
        reward = 0
        info = {'effective_action': False}
        if direction == 'R':
            if self.state[1] + 1 < self.col:
                if self.maze[self.state[0], self.state[1] + 1] == 0:
                    self.state = (self.state[0], self.state[1] + 1)
                    reward = -1
                    info['effective_action'] = True
        elif direction == 'L':
            if self.state[1] > 0:
                if self.maze[self.state[0], self.state[1] - 1] == 0:
                    self.state = (self.state[0], self.state[1] - 1)
                    reward = -1
                    info['effective_action'] = True
        elif direction == 'D':
            if self.state[0] + 1 < self.row:
                if self.maze[self.state[0] + 1, self.state[1]] == 0:
                    self.state = (self.state[0] + 1, self.state[1])
                    reward = -1
                    info['effective_action'] = True
        elif direction == 'U':
            if self.state[0] > 0:
                if self.maze[self.state[0] - 1, self.state[1]] == 0:
                    self.state = (self.state[0] - 1, self.state[1])
                    reward = -1
                    info['effective_action'] = True
        else:
            raise ValueError(
                'The args "direction" should be "R", "L", "D" or "U" either.')

        is_terminated = self.state == self.goal

        return (self.state, reward, is_terminated, info)

    def get_maze_color(self, v_value):
        colors = np.zeros((*self.maze.shape, 3))
        colors[self.maze == 0] = 1

        if v_value is not None:
            v = v_value * (1 - self.maze)
            max_v = np.max(v)
            min_v = np.min(v)
            h = (max_v - v) / (max_v - min_v) * 4
            x = 1 - np.abs(h % 2 - 1)

            triplets = [
                [np.ones_like(x), x, np.zeros_like(x)],
                [x, np.ones_like(x), np.zeros_like(x)],
                [np.zeros_like(x), np.ones_like(x), x],
                [np.zeros_like(x), x, np.ones_like(x)],
            ]
            for i, triplet in enumerate(triplets):
                cond = (i <= h) * (h <= i + 1) * (self.maze == 0)
                colors[:, :, 0][cond] = triplet[0][cond]
                colors[:, :, 1][cond] = triplet[1][cond]
                colors[:, :, 2][cond] = triplet[2][cond]

        colors *= 255
        colors = np.clip(colors, 0, 255).astype(np.int)

        return colors

    def is_goal(self, state):
        return self.goal == state

    def is_wall(self, state):
        return self.maze[state] == 1

    def get_initial_q_value(self):
        q_value_shape = tuple(list(self.maze.shape) + [4])
        q_value = np.random.uniform(low=0, high=1, size=q_value_shape)

        directions = ['R', 'L', 'D', 'U']
        for y in range(self.maze.shape[0]):
            for x in range(self.maze.shape[1]):
                if self.maze[y, x] == 1:
                    q_value[y, x] = -1000
                    continue
                for i, direction in enumerate(directions):
                    self.locate((y, x))
                    _, _, _, info = self.step(direction)
                    if not info['effective_action']:
                        q_value[y, x, i] = -1000

        return q_value

    def get_initial_v_value(self):
        v_value = np.random.uniform(low=0, high=1, size=self.maze.shape)
        v_value[self.maze == 1] = -1000
        v_value[self.goal] = 0
        return v_value


def get_action_for_v_value(env, v_value, state):
    directions = ['R', 'L', 'D', 'U']
    max_v = None
    for direction in directions:
        next_state, _, _, info = env.step(direction)
        if info['effective_action'] and (
                max_v is None or max_v < v_value[next_state]):
            action = direction
            max_v = v_value[next_state]
        env.locate(state)

    return action


def get_action_for_q_value(env, q_value, state, epsilon):
    directions = ['R', 'L', 'D', 'U']
    max_q = None
    possible_pairs = []
    for i, direction in enumerate(directions):
        _, _, _, info = env.step(direction)
        if info['effective_action']:
            possible_pairs.append((direction, i))
            if max_q is None or max_q < q_value[state][i]:
                action = direction
                action_index = i
                max_q = q_value[state][i]
        env.locate(state)

    if np.random.uniform() < epsilon:
        return random.sample(possible_pairs, 1)[0]

    return action, action_index


class ValueIterTrainer:
    def __init__(
            self,
            warm_up_iter_count: int = 100,
            iter_count: int = 20,
            max_steps: int = 1000,
            gamma: float = 0.95,

        maze_text: str = None,
    ):
        self.env = MazeEnvironment(maze_text)
        self.v_value = self.env.get_initial_v_value()

        self.warm_up_iter_count = warm_up_iter_count
        self.iter_count = iter_count
        self.max_steps = max_steps
        self.gamma = gamma

        self.iter_start = True
        self.curr_iter = 0
        self.curr_step = 0

    def update_v_value(self):
        for i in range(self.env.row):
            for j in range(self.env.col):
                state = (i, j)
                if self.env.is_wall(state) or self.env.is_goal(state):
                    continue
                new_vs = []
                for direction in ['R', 'L', 'D', 'U']:
                    self.env.locate(state)
                    next_state, reward, _, info = self.env.step(direction)
                    if info['effective_action']:
                        new_vs.append(
                            reward + self.gamma * self.v_value[next_state])
                self.v_value[state] = max(new_vs)

    def warm_up(self):
        for _ in range(self.warm_up_iter_count):
            self.update_v_value()

    def run(self):
        if self.iter_start:
            if self.curr_iter >= self.iter_count:
                return {
                    'finished': True,
                    'v_value': self.v_value.tolist(),
                    'current_position': self.env.state,
                }
            self.curr_iter += 1
            self.curr_step = 0

            self.update_v_value()
            self.prev_state = self.env.reset()

            self.iter_start = False

        else:
            self.curr_step += 1
            action = get_action_for_v_value(
                self.env, self.v_value, self.prev_state)
            state, _, is_terminated, _ = self.env.step(action)

            self.prev_state = state
            if is_terminated or self.curr_step >= self.max_steps:
                self.iter_start = True

        colors = self.env.get_maze_color(self.v_value)
        rgbs = [[''.join([f'{x:02x}' for x in w]) for w in v] for v in colors]

        return {
            'rgb': rgbs,
            'current_position': self.env.state,
            'iteration': self.curr_iter,
            'step': self.curr_step,
        }


class SarsaLambdaTrainer:
    def __init__(
            self,
            warm_up_iter_count: int = 100,
            iter_count: int = 20,
            max_steps: int = 1000,
            gamma: float = 0.95,

            alpha: float = 0.1,
            epsilon: float = 0.1,
            lambda_value: float = 0.2,

        maze_text: str = None,
    ):
        self.env = MazeEnvironment(maze_text)
        self.q_value = self.env.get_initial_q_value()

        self.warm_up_iter_count = warm_up_iter_count
        self.iter_count = iter_count
        self.max_steps = max_steps
        self.gamma = gamma

        self.alpha = alpha * (1 - lambda_value)
        self.epsilon = epsilon
        self.lambda_value = lambda_value

        self.iter_start = True
        self.curr_iter = 0
        self.curr_step = 0

        self.z = np.zeros_like(self.q_value)
        self.q_value_old = 0

        self.goal_reward = 10

    def warm_up(self):
        for _ in range(self.warm_up_iter_count):
            self.curr_epsilon = self.epsilon * \
                (1 - self.curr_iter / self.iter_count)

            self.z = np.zeros_like(self.q_value)
            self.q_value_old = 0

            self.prev_state = self.env.reset()
            self.prev_action, self.prev_action_index = get_action_for_q_value(
                self.env, self.q_value, self.prev_state, self.curr_epsilon)

            for _ in range(self.max_steps):
                state, reward, is_terminated, _ = self.env.step(
                    self.prev_action)
                reward = self.goal_reward if is_terminated and self.curr_step < int(
                    self.max_steps * 0.975) else -1
                action, action_index = get_action_for_q_value(
                    self.env, self.q_value, state, self.curr_epsilon)

                if self.prev_action is not None:
                    delta = reward + self.gamma * \
                        self.q_value[state][action_index] - \
                        self.q_value[self.prev_state][self.prev_action_index]

                    x = np.zeros_like(self.q_value)
                    x[self.prev_state][self.prev_action_index] = 1
                    z = self.gamma * self.lambda_value * self.z + \
                        (1 - self.alpha * self.gamma * self.lambda_value *
                         self.z[self.prev_state][self.prev_action_index]) * x

                    self.q_value += self.alpha * \
                        (delta + self.q_value[self.prev_state]
                         [self.prev_action_index] - self.q_value_old) * z
                    self.q_value -= self.alpha * \
                        (self.q_value[self.prev_state]
                         [self.prev_action_index] - self.q_value_old) * x
                    self.q_value_old = self.q_value[state][action_index]

                self.prev_state = state
                self.prev_action = action
                self.prev_action_index = action_index

                if is_terminated or self.curr_step >= self.max_steps:
                    break

    def run(self):
        self.epsilon = 0
        if self.iter_start:
            if self.curr_iter >= self.iter_count:
                return {
                    'finished': True,
                    'q_value': self.q_value.tolist(),
                    'current_position': self.env.state,
                }
            self.curr_iter += 1
            self.curr_step = 0
            self.curr_epsilon = self.epsilon * \
                (1 - self.curr_iter / self.iter_count)

            self.z = np.zeros_like(self.q_value)
            self.q_value_old = 0

            self.prev_state = self.env.reset()
            self.prev_action, self.prev_action_index = get_action_for_q_value(
                self.env, self.q_value, self.prev_state, self.curr_epsilon)

            self.iter_start = False

        else:
            self.curr_step += 1
            state, reward, is_terminated, _ = self.env.step(self.prev_action)
            reward = self.goal_reward if is_terminated and self.curr_step < int(
                self.max_steps * 0.975) else -1
            action, action_index = get_action_for_q_value(
                self.env, self.q_value, state, self.curr_epsilon)

            if self.prev_action is not None:
                delta = reward + self.gamma * \
                    self.q_value[state][action_index] - \
                    self.q_value[self.prev_state][self.prev_action_index]

                x = np.zeros_like(self.q_value)
                x[self.prev_state][self.prev_action_index] = 1
                z = self.gamma * self.lambda_value * self.z + \
                    (1 - self.alpha * self.gamma * self.lambda_value *
                     self.z[self.prev_state][self.prev_action_index]) * x

                self.q_value += self.alpha * \
                    (delta + self.q_value[self.prev_state]
                     [self.prev_action_index] - self.q_value_old) * z
                self.q_value -= self.alpha * \
                    (self.q_value[self.prev_state]
                     [self.prev_action_index] - self.q_value_old) * x
                self.q_value_old = self.q_value[state][action_index]

            self.prev_state = state
            self.prev_action = action
            self.prev_action_index = action_index

            if is_terminated or self.curr_step >= self.max_steps:
                self.iter_start = True

        v_value = np.max(self.q_value, axis=2)
        colors = self.env.get_maze_color(v_value)
        rgbs = [[''.join([f'{x:02x}' for x in w]) for w in v] for v in colors]
        return {
            'rgb': rgbs,
            'current_position': self.env.state,
            'iteration': self.curr_iter,
            'step': self.curr_step,
        }
