# update.py

import random

def calculate_dynamic_quarantine_rate(G, quarantine_rate_max):
    infected = sum(1 for n in G.nodes if G.nodes[n]["state"] == "I")
    return quarantine_rate_max * (1 - infected / len(G.nodes))


def apply_infection(G, infection_prob):
    new_states = {}
    for node in G.nodes:
        if G.nodes[node]["state"] in ["I", "Q"]:
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor]["state"] == "S" and random.random() < infection_prob:
                    new_states[neighbor] = "I"
    return new_states


def update_states(G, new_states, recovery_time, immunity_duration, quarantine_edges):
    for node in G.nodes:
        node_data = G.nodes[node]
        state = node_data["state"]

        if state == "I":
            node_data["days_infected"] += 1
            if node_data["days_infected"] >= recovery_time:
                new_states[node] = "R"
                node_data["days_immune"] = 0

        elif state == "R":
            node_data["days_immune"] += 1
            if node_data["days_immune"] >= immunity_duration:
                new_states[node] = "S"

        elif state == "Q":
            node_data["days_in_quarantine"] += 1
            if node_data["days_in_quarantine"] >= 2:
                new_states[node] = "I"
                node_data["days_infected"] = 0
                G.add_edges_from(quarantine_edges.pop(node, []))

    for node, state in new_states.items():
        G.nodes[node]["state"] = state
        if state in ["S", "I"]:
            G.nodes[node]["days_infected"] = 0


def apply_vaccination(G, step, vaccine_start_day, vaccination_rate):
    if step >= vaccine_start_day:
        susceptibles = [n for n in G.nodes if G.nodes[n]["state"] == "S"]
        if susceptibles:
            num_to_vaccinate = max(1, int(vaccination_rate * len(susceptibles)))
            vaccinated = random.sample(susceptibles, min(num_to_vaccinate, len(susceptibles)))
            for v in vaccinated:
                G.nodes[v]["state"] = "V"
            return True, len(vaccinated)
    return False, 0


def apply_quarantine(G, dynamic_quarantine_rate, quarantine_edges):
    for node in G.nodes:
        if G.nodes[node]["state"] == "I" and random.random() < dynamic_quarantine_rate:
            G.nodes[node]["state"] = "Q"
            quarantine_edges[node] = list(G.edges(node))
            G.remove_edges_from(quarantine_edges[node])
            G.nodes[node]["days_in_quarantine"] = 0
