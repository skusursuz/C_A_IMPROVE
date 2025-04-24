import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Standard Library ===
import csv
import random
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, BooleanVar, Checkbutton
from itertools import count

# === Third-Party Libraries ===
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation



# === Local Imports ===
from Model.Params.constants import (
    SLIDER_CONFIGS,
    PRESETS,
    STRATEGY_CONFIGS,
    n,
    p_edge,
    quarantine_rate,
    num_hubs,
)
from Model.Params.utils import create_slider
from Controller.record import save_history_to_csv
from Controller.update import (
    apply_infection,
    update_states,
    apply_quarantine,
    apply_vaccination,
    calculate_dynamic_quarantine_rate,
    apply_contact_quarantine,
)



degree_distribution = {
    1: 0.5,
    2: 0.4,
    3: 0.2,
}

def custom_graph(n, degree_distribution):
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

# -----------------------------
# Classe principale de l'application
# -----------------------------

class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation Épidémique Interactive")

        # === PANNEAU DE CONTRÔLE (À GAUCHE) ===

        control_frame = ttk.Frame(root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=10)

        # === Paramètres (Sliders) ===
        
        params_frame = ttk.LabelFrame(control_frame, text="Paramètres")
        params_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        for slider in SLIDER_CONFIGS:
            slider_widget = create_slider(
                params_frame,
                slider["label"],
                slider["from_"],
                slider["to"],
                slider["default"],
                slider["row"],
            )
            setattr(self, slider["attr"], slider_widget)

        # === Stratégies de confinement (Checkboxes) ===

        strategy_frame = ttk.LabelFrame(control_frame, text="Stratégies de confinement")
        strategy_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        for strategy in STRATEGY_CONFIGS:
            var = BooleanVar(value=True)

            def on_toggle(s=strategy, v=var):
                status = "activée" if v.get() else "désactivée"
                print(f"{s['label']} : stratégie {status}")

            chk = Checkbutton(
                strategy_frame,
                text=strategy["label"],
                variable=var,
                command=on_toggle
            )
            chk.grid(row=strategy["row"], column=0, sticky="w")
            setattr(self, strategy["attr"], var)

        # === Options de préréglage ===

        preset_frame = ttk.Frame(control_frame)
        preset_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        self.preset_label = ttk.Label(preset_frame, text="Paramètres prédéfinis :")
        self.preset_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))

        self.covid_button = ttk.Button(preset_frame, text="COVID-19", command=self.set_covid_params)
        self.covid_button.grid(row=1, column=0, padx=5)

        self.spanish_flu_button = ttk.Button(preset_frame, text="Grippe espagnole", command=self.set_spanish_flu_params)
        self.spanish_flu_button.grid(row=1, column=1, padx=5)

        
        # === Bouton pour lancer la simulation ===

        self.start_button = ttk.Button(
            control_frame, text="▶ Lancer la simulation", command=self.start_simulation
        )
        self.start_button.grid(row=3, column=0, columnspan=2, pady=15)

        # === PANNEAU DE GRAPHIQUES (À DROITE, EN HAUT ET EN BAS) ===
        self.canvas_frame = ttk.Frame(root, width=900, height=900)
        self.canvas_frame.pack_propagate(False)  # Boyutun dışarıdan değişmesini engelle
        self.canvas_frame.pack(side=tk.RIGHT, padx=10, pady=10)


        

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(7, 9))

        
        self.credit_label = tk.Label(
            control_frame,
            text="SELIM KUSURSUZ, NADJIB ATAMNIA\nUNIVERSITÉ PARIS-SACLAY",
            fg="purple", 
            font=("Helvetica", 15, "italic"),
            justify="left"
        )
        self.credit_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 10))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.ani = None


    def apply_preset(self, preset_name):
        preset = PRESETS.get(preset_name)
        if preset:
            for attr, value in preset.items():
                if hasattr(self, attr):
                    getattr(self, attr).set(value)

    def set_covid_params(self):
        self.apply_preset("COVID-19")

    def set_spanish_flu_params(self):
        self.apply_preset("Grippe espagnole")

    def start_simulation(self):
        if self.ani:
            try:
                self.ani.event_source.stop()
            except Exception:
                pass

        self.ax1.clear()
        self.ax2.clear()
        self.quarantine_rate_max = self.quarantine_slider.get()

        params = {
            "infection_prob": self.infection_slider.get(),
            "recovery_time": int(self.recovery_slider.get()),
            "vaccination_rate": self.vaccination_slider.get(),
            "vaccination_acceleration": self.vaccination_acceleration_slider.get(), 
            "vaccine_start_day": int(self.vaccine_day_slider.get()),
        }

        threading.Thread(target=self.run_simulation, kwargs=params, daemon=False).start()


    def run_simulation(self, infection_prob, recovery_time, vaccination_rate, vaccination_acceleration, vaccine_start_day):
        self.setup_simulation(infection_prob, recovery_time, vaccination_rate, vaccination_acceleration, vaccine_start_day)
        self.ani = animation.FuncAnimation(self.fig, self.update, frames=count(), interval=300, repeat=False)
        self.canvas.draw()


    def setup_simulation(self, infection_prob, recovery_time, vaccination_rate, vaccination_acceleration, vaccine_start_day):
        self.G = custom_graph(n=n, degree_distribution=degree_distribution)
        raw_pos = nx.circular_layout(self.G)
        self.pos = {node: (x * 300, y * 800) for node, (x, y) in raw_pos.items()}
        self.quarantine_edges = {}
        self.to_quarantine = []

        self.color_map = {
            "S": "blue",
            "I": "red",
            "R": "green",
            "V": "orange",
            "Q": "purple",
        }

        self.history = {k: [] for k in self.color_map}
        self.pending_infections = []

        self.vaccination_rate = vaccination_rate
        self.vaccination_acceleration = vaccination_acceleration 
        self.vaccine_start_day = vaccine_start_day
        self.vaccine_applied = False

        hub_nodes = random.sample(list(self.G.nodes), num_hubs)
        for node in self.G.nodes:
            self.G.nodes[node].update(state="S", days_infected=0, days_immune=0, days_in_quarantine=0)
            if node not in hub_nodes:
                self.G.add_edge(node, random.choice(hub_nodes))

        patient_zero = random.choice(list(self.G.nodes))
        self.G.nodes[patient_zero]["state"] = "I"

        self.step = 0
        self.infection_prob = infection_prob
        self.recovery_time = recovery_time


    def get_colors(self):
        return [self.color_map.get(self.G.nodes[n]["state"], "gray") for n in self.G.nodes]

    def update(self, frame):
        self.step += 1

        # === Contrôle de la stratégie de quarantaine ===

        strategy_1 = self.strategy_1_active.get()
        strategy_2 = self.strategy_2_active.get()

        if strategy_1 and not strategy_2:
            dynamic_rate = calculate_dynamic_quarantine_rate(self.G, self.quarantine_slider.get())
            apply_quarantine(self.G, dynamic_rate, self.quarantine_edges)

        elif strategy_2 and not strategy_1:
            apply_contact_quarantine(self.G, self.quarantine_edges)

        elif strategy_1 and strategy_2:
            dynamic_rate = calculate_dynamic_quarantine_rate(self.G, self.quarantine_slider.get())
            apply_quarantine(self.G, dynamic_rate, self.quarantine_edges)
            apply_contact_quarantine(self.G, self.quarantine_edges)

        else:
            print("⚠️ Aucun stratégie de quarantaine sélectionnée — pas de confinement appliqué.")

        # === Gecikmiş Enfeksiyonları İşle ===
        new_symptomatic = []
        remaining_pending = []
        for node, days_left in self.pending_infections:
            if days_left - 1 <= 0:
                new_symptomatic.append(node)
            else:
                remaining_pending.append((node, days_left - 1))
        self.pending_infections = remaining_pending

        # === Traiter les infections différées ===

        for node in new_symptomatic:
            self.G.nodes[node]["state"] = "I"
            self.G.nodes[node]["days_infected"] = 0
            self.G.nodes[node]["days_symptomatic"] = 0
            self.to_quarantine.append(node)

        # === Quarantaine après 1 jour (si stratégie active uniquement) ===

        if strategy_1 or strategy_2:
            still_pending = []
            for node in self.to_quarantine:
                self.G.nodes[node]["days_symptomatic"] += 1
                if self.G.nodes[node]["days_symptomatic"] >= 1:
                    self.quarantine_edges[node] = list(self.G.edges(node))
                    self.G.remove_edges_from(self.quarantine_edges[node])
                    self.G.nodes[node]["days_in_quarantine"] = 0
                else:
                    still_pending.append(node)
            self.to_quarantine = still_pending
        else:
            
            # Si aucune stratégie n’est sélectionnée, pas de quarantaine

            self.to_quarantine.clear()

        # === Ajouter les nouvelles infections ===

        apply_infection(self.G, self.infection_prob, self.pending_infections)

         # === Application de la vaccination ===
        if self.step >= self.vaccine_start_day:
            applied, num_vaccinated = apply_vaccination(
                self.G, self.step, self.vaccine_start_day, self.vaccination_rate, self.vaccination_acceleration
            )
            if applied:
                print(f"Aşı uygulandı. Gün: {self.step}, Kişi sayısı: {num_vaccinated}")


        # === L’épidémie est-elle terminée ? ===

        if not any(self.G.nodes[n]["state"] == "I" for n in self.G.nodes):
            print(f"Épidémie terminée au jour {frame + 1}")
            if self.ani:
                self.ani.event_source.stop()
                save_history_to_csv(self)
            return

    # === Mise à jour des états ===

        new_states = {}
        update_states(self.G, new_states, self.recovery_time, self.quarantine_edges)


        # === Mise à jour des graphiques ===

        self.ax1.clear()
        nx.draw(self.G, self.pos, node_color=self.get_colors(), node_size=20, ax=self.ax1)
        
        self.ax1.set_title(f"Étape {frame + 1}")
        self.ax1.axis("off")

        total_nodes = len(self.G.nodes)
        for key in self.history:
            if key == "S":
                count = sum(1 for node in self.G.nodes if self.G.nodes[node]["state"] in ["S", "Q", "V"]) / total_nodes
            else:
                count = sum(1 for node in self.G.nodes if self.G.nodes[node]["state"] == key) / total_nodes
            self.history[key].append(count)

        self.ax2.clear()
        for key, values in self.history.items():
            self.ax2.plot(values, label=key, color=self.color_map[key])

        self.ax2.set_ylim(0, 1)
        self.ax2.legend()
        self.ax2.set_title("Évolution")
        self.ax2.set_xlabel("Temps")
        self.ax2.set_ylabel("Proportion")

        self.canvas.draw()
