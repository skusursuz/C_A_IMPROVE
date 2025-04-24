# Params/graph.py içine koyulacak kod
import networkx as nx
import random

def custom_graph(n, degree_distribution=None):
    if degree_distribution is None:
        degree_distribution = {1: 0.5, 2: 0.4, 3: 0.2}

    G = nx.Graph()
    G.add_nodes_from(range(n))

    degrees = random.choices(
        population=list(degree_distribution.keys()),
        weights=list(degree_distribution.values()),
        k=n,
    )
    target_degrees = {node: deg for node, deg in zip(G.nodes, degrees)}
    nodes = list(G.nodes)
    random.shuffle(nodes)

    for node in nodes:
        while G.degree[node] < target_degrees[node]:
            potential_targets = [
                target for target in nodes
                if target != node
                and not G.has_edge(node, target)
                and G.degree[target] < target_degrees[target]
            ]
            if not potential_targets:
                break
            target = random.choice(potential_targets)
            G.add_edge(node, target)

    return G
