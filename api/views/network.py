from collections import deque
import numpy as np


class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []

    @property
    def node_size(self):
        return len(self.nodes)

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges.append(edge)


def to_network_json(graph, is_expanded=True):
    edges = []

    adjacency_list = [[] for _ in range(graph.node_size)]
    is_child = np.zeros(len(graph.nodes), dtype=bool)
    for edge in graph.edges:
        adjacency_list[edge['from']].append(edge['to'])
        edges.append({
            'from': edge['from'],
            'to': edge['to'],
            'length': edge['length'],
            'arrows': 'to',
        })
        is_child[edge['to']] = True

    parent_node_indices = []
    for i, is_chi in enumerate(is_child):
        if not is_chi:
            parent_node_indices.append(i)
    parent_node_index_set = set(parent_node_indices)

    nodes = []
    parent2childs = {}
    is_visited = np.zeros(len(graph.nodes), dtype=bool)

    def dps(deq, depth):
        if not deq:
            return

        parent_node_index = deq.pop()
        parent_node = graph.nodes[parent_node_index]

        node_set = set()
        for child_node_index in adjacency_list[parent_node_index]:
            if is_visited[child_node_index]:
                continue

            deq.append(child_node_index)
            is_visited[child_node_index] = True

            child_node_set = dps(deq, depth + 1)
            node_set = node_set.union(child_node_set)

        is_shown = is_expanded or parent_node['id'] in parent_node_index_set
        is_hidden = not is_shown
        color = 'blue'
        if is_expanded:
            color = 'red'
        if not node_set:
            color = 'green'

        nodes.append({
            'id': parent_node['id'],
            'label': parent_node['label'],
            'hidden_count': 0 if is_expanded else depth,
            'hidden': is_hidden,
            'expanded': is_expanded,
            'color': color,
        })

        if node_set:
            parent2childs[parent_node['id']] = list(node_set)
        node_set.add(parent_node['id'])

        return node_set

    for parent_node_index in parent_node_indices:
        deq = deque()

        deq.append(parent_node_index)
        is_visited[parent_node_index] = True

        dps(deq, 0)

    return {
        'nodes': nodes,
        'edges': edges,
        'parent2childs': parent2childs
    }


def get_network_json():
    graph = Graph()
    for i in range(8):
        graph.add_node({
            'id': i,
            'label': f'Node{i}',
        })

    graph.add_edge({'from': 0, 'to': 2, 'length': 10})
    graph.add_edge({'from': 1, 'to': 0, 'length': 10})
    graph.add_edge({'from': 1, 'to': 3, 'length': 10})
    graph.add_edge({'from': 1, 'to': 4, 'length': 200})
    graph.add_edge({'from': 1, 'to': 5, 'length': 10})
    graph.add_edge({'from': 1, 'to': 6, 'length': 10})
    graph.add_edge({'from': 7, 'to': 1, 'length': 10})

    network_json = to_network_json(graph, False)

    return network_json
