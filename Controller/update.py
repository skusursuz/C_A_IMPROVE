# update.py
import math  # Fonksiyonun başında gerekli

import random
import networkx as nx

def calculate_dynamic_quarantine_rate(G, quarantine_rate_max):
    infected = sum(1 for n in G.nodes if G.nodes[n]["state"] == "I")
    return quarantine_rate_max * (1 - infected / len(G.nodes))


def apply_infection(G, infection_prob, pending_infections):
    already_pending = {node for node, _ in pending_infections}

    for node in G.nodes:
        if G.nodes[node]["state"] == "I":  # Sadece enfekte olan yayabilir
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor]["state"] == "S" and neighbor not in already_pending:
                    if random.random() < infection_prob:
                        delay = random.randint(1, 3)  # <- BU EKLENSİN
                        pending_infections.append((neighbor, delay))

                        
def update_states(G, new_states, recovery_time, quarantine_edges):
    for node in G.nodes:
        node_data = G.nodes[node]
        state = node_data["state"]

        if state == "I":
            node_data["days_infected"] += 1
            if node_data["days_infected"] >= recovery_time:
                new_states[node] = "R"  # Kalıcı bağışıklık
                node_data["days_immune"] = 0  # Bu artık güncellenmeyecek ama resetle iyi olur

        elif state == "Q":
            node_data["days_in_quarantine"] += 1
            if node_data["days_in_quarantine"] >= recovery_time:
                new_states[node] = "I"
                node_data["days_infected"] = 0
                edges = quarantine_edges.pop(node, [])
                if edges:
                    G.add_edges_from(edges)

    # Durum geçişlerini uygula
    for node, state in new_states.items():
        G.nodes[node]["state"] = state
        if state in ["S", "I"]:
            G.nodes[node]["days_infected"] = 0


def apply_vaccination(G, step, vaccine_start_day, vaccination_rate, vaccination_acceleration):
    if step >= vaccine_start_day:
        susceptibles = [n for n in G.nodes if G.nodes[n]["state"] == "S"]
        if susceptibles:
            # Tutarlı artış için logaritmik bir artış modeli kullanalım
            if vaccination_acceleration == 0:
                effective_rate = vaccination_rate
            else:
                # Logaritmik artış (yavaş başlar, giderek artar ama doygunlaşır)
                effective_rate = vaccination_rate + vaccination_acceleration * math.log1p(step - vaccine_start_day)

            # Üst sınır: %100'ü geçemez
            effective_rate = min(effective_rate, 1.0)

            # Günlük maksimum aşılanabilecek kişi sınırı (örnek: max 50 kişi/gün)
            max_daily_vaccinations = 50
            num_to_vaccinate = min(max_daily_vaccinations, int(effective_rate * len(susceptibles)))

            # Aşılamayı uygula
            vaccinated = random.sample(susceptibles, min(num_to_vaccinate, len(susceptibles)))
            for v in vaccinated:
                G.nodes[v]["state"] = "V"

            # Konsola bilgi ver (görsel takip için)
            print(f"[Gün {step}] Aşılama oranı: {effective_rate:.3f} | Aşılanan kişi: {len(vaccinated)}")
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
    
    # Her bireyin kendi bağlantılarını kaldır
    for node in to_quarantine:
        quarantine_edges[node] = list(G.edges(node))
        G.remove_edges_from(quarantine_edges[node])
        G.nodes[node]["state"] = "Q"
        G.nodes[node]["days_in_quarantine"] = 0

    # Karantinadaki bireylerin birbirleriyle olan bağlantılarını da kaldır
    quarantined_list = list(to_quarantine)
    for i in range(len(quarantined_list)):
        for j in range(i + 1, len(quarantined_list)):
            u, v = quarantined_list[i], quarantined_list[j]
            if G.has_edge(u, v):
                G.remove_edge(u, v)
                # Bunları da kaydetmek istersen quarantine_edges'e ekleyebilirsin:
                quarantine_edges.setdefault(u, []).append((u, v))
                quarantine_edges.setdefault(v, []).append((u, v))
