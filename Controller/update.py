import math  
import random
import networkx as nx

def calculate_dynamic_quarantine_rate(G, quarantine_rate_max):
    infected = sum(1 for n in G.nodes if G.nodes[n]["state"] == "I")
    return quarantine_rate_max * (1 - infected / len(G.nodes))


def apply_infection(G, infection_prob, pending_infections):
    already_pending = {node for node, _ in pending_infections}

    for node in G.nodes:
        if G.nodes[node]["state"] == "I":  # Seuls les infectés peuvent propager
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor]["state"] == "S" and neighbor not in already_pending:
                    if random.random() < infection_prob:
                        delay = random.randint(1, 3)  # <- À AJOUTER
                        pending_infections.append((neighbor, delay))


def update_states(G, new_states, recovery_time, quarantine_edges):
    for node in G.nodes:
        node_data = G.nodes[node]
        state = node_data["state"]

        if state == "I":
            node_data["days_infected"] += 1
            if node_data["days_infected"] >= recovery_time:
                new_states[node] = "R"  # Immunité permanente
                node_data["days_immune"] = 0  # Ne sera plus mis à jour, mais on le réinitialise par prudence

        elif state == "Q":
            node_data["days_in_quarantine"] += 1
            if node_data["days_in_quarantine"] >= recovery_time:
                new_states[node] = "I"
                node_data["days_infected"] = 0
                edges = quarantine_edges.pop(node, [])
                if edges:
                    G.add_edges_from(edges)

    # Appliquer les transitions d'état
    for node, state in new_states.items():
        G.nodes[node]["state"] = state
        if state in ["S", "I"]:
            G.nodes[node]["days_infected"] = 0


def apply_vaccination(G, step, vaccine_start_day, vaccination_rate, vaccination_acceleration):
    if step >= vaccine_start_day:
        susceptibles = [n for n in G.nodes if G.nodes[n]["state"] == "S"]
        if susceptibles:
            # Utilisation d’un modèle de croissance logarithmique pour une augmentation cohérente
            if vaccination_acceleration == 0:
                effective_rate = vaccination_rate
            else:
                # Croissance logarithmique (commence lentement, puis accélère et se stabilise)
                effective_rate = vaccination_rate + vaccination_acceleration * math.log1p(step - vaccine_start_day)

            # Limite supérieure : ne peut pas dépasser 100 %
            effective_rate = min(effective_rate, 1.0)

            # Nombre maximum de vaccinations quotidiennes (ex. : max 50 personnes/jour)
            max_daily_vaccinations = 50
            num_to_vaccinate = min(max_daily_vaccinations, int(effective_rate * len(susceptibles)))

            # Appliquer la vaccination
            vaccinated = random.sample(susceptibles, min(num_to_vaccinate, len(susceptibles)))
            for v in vaccinated:
                G.nodes[v]["state"] = "V"

            # Afficher dans la console (suivi visuel)
            print(f"[Jour {step}] Taux de vaccination : {effective_rate:.3f} | Nombre de vaccinés : {len(vaccinated)}")
            return True, len(vaccinated)
    return False, 0


def apply_quarantine(G, dynamic_quarantine_rate, quarantine_edges):
    for node in G.nodes:
        if G.nodes[node]["state"] == "I" and random.random() < dynamic_quarantine_rate:
            G.nodes[node]["state"] = "Q"
            quarantine_edges[node] = list(G.edges(node))
            G.remove_edges_from(quarantine_edges[node])
            G.nodes[node]["days_in_quarantine"] = 0


def apply_contact_quarantine(G, quarantine_edges):
    to_quarantine = set()

    for node in G.nodes:
        if G.nodes[node]["state"] == "I":
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor]["state"] == "S":
                    to_quarantine.add(neighbor)

    # Supprimer les connexions individuelles de chaque personne
    for node in to_quarantine:
        quarantine_edges[node] = list(G.edges(node))
        G.remove_edges_from(quarantine_edges[node])
        G.nodes[node]["state"] = "Q"
        G.nodes[node]["days_in_quarantine"] = 0

    # Supprimer également les connexions entre les personnes en quarantaine
    quarantined_list = list(to_quarantine)
    for i in range(len(quarantined_list)):
        for j in range(i + 1, len(quarantined_list)):
            u, v = quarantined_list[i], quarantined_list[j]
            if G.has_edge(u, v):
                G.remove_edge(u, v)
                # Si souhaité, enregistrer aussi ces liens dans quarantine_edges :
                quarantine_edges.setdefault(u, []).append((u, v))
                quarantine_edges.setdefault(v, []).append((u, v))
