import csv
import tkinter as tk
from tkinter import ttk
from itertools import count
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import random
from datetime import datetime
import threading
from constants import SLIDER_CONFIGS
from constants import PRESETS  # Bunu en üst import kısmına ekle

from update import (
    apply_infection,
    update_states,
    apply_quarantine,
    apply_vaccination,
    calculate_dynamic_quarantine_rate,
)

from constants import n, p_edge, quarantine_rate, num_hubs
from utils import create_slider

degree_distribution = {
    1: 0.5,
    2: 0.4,
    3: 0.2,
}

def apply_preset(self, preset_name):
        preset = PRESETS.get(preset_name)
        if preset:
            for attr, value in preset.items():
                getattr(self, attr).set(value)

        def set_covid_params(self):
            self.apply_preset("COVID-19")

        def set_spanish_flu_params(self):
            self.apply_preset("Grippe espagnole")
        
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
                n
                for n in nodes
                if n != node
                and not G.has_edge(node, n)
                and G.degree[n] < target_degrees[n]
            ]
            if not potential_targets:
                break
            target = random.choice(potential_targets)
            G.add_edge(node, target)

    return G


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation Épidémique Interactive")

        control_frame = ttk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        for slider in SLIDER_CONFIGS:
            slider_widget = create_slider(
                control_frame,
                slider["label"],
                slider["from_"],
                slider["to"],
                slider["default"],
                slider["row"],
            )
            setattr(self, slider["attr"], slider_widget)

        self.preset_label = ttk.Label(control_frame, text="Paramètres prédéfinis :")
        self.preset_label.grid(row=7, column=0, columnspan=2, pady=(6, 0))

        self.covid_button = ttk.Button(
            control_frame, text="COVID-19", command=self.set_covid_params
        )
        self.covid_button.grid(row=8, column=0, pady=5)

        self.spanish_flu_button = ttk.Button(
            control_frame, text="Grippe espagnole", command=self.set_spanish_flu_params
        )
        self.spanish_flu_button.grid(row=8, column=1, pady=5)

        self.start_button = ttk.Button(
            control_frame, text="Lancer la simulation", command=self.start_simulation
        )
        self.start_button.grid(row=9, column=0, columnspan=2, pady=10)

        self.canvas_frame = ttk.Frame(root)
        self.canvas_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.ani = None

    def apply_preset(self, preset_name):
        preset = PRESETS.get(preset_name)
        if preset:
            for attr, value in preset.items():
                getattr(self, attr).set(value)

    def set_covid_params(self):
        self.apply_preset("COVID-19")

    def set_spanish_flu_params(self):
        self.apply_preset("Grippe espagnole")

    def save_history_to_csv(self, filename=None):
        """
        Simülasyon verilerini CSV'ye, grafiği ve metinli özetini PDF'e kaydeder.
        """
        if filename is None:
            today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{today}_simulation_result.csv"

        pdf_filename = filename.replace(".csv", ".pdf")

        # Sıralama sabit kalsın
        states = ["S", "I", "R", "V", "Q"]

        try:
            steps = len(next(iter(self.history.values())))
        except (StopIteration, TypeError):
            print("Kayıt edilecek geçmiş veri bulunamadı.")
            return

        # CSV Kayıt
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Temps"] + states)
            for i in range(steps):
                row = [i] + [self.history.get(state, [0]*steps)[i] for state in states]
                writer.writerow(row)

        print(f"Simülasyon geçmişi CSV olarak kaydedildi: {filename}")

        # PDF Grafik + Metin
        fig, ax = plt.subplots(figsize=(10, 6))

        # Grafik çizimi
        for state in states:
            ax.plot(self.history[state], label=state)

        ax.set_title("Évolution des états dans la population")
        ax.set_xlabel("Temps (jours)")
        ax.set_ylabel("Proportion")
        ax.set_ylim(0, 1)
        ax.legend()

        # METIN: Parametreler
        text_x = 1.02
        text_y = 0.9
        spacing = 0.06

        param_text = [
            f"Durée totale: {self.step} jours",
            f"Infection: {self.infection_prob:.2f}",
            f"Rétablissement: {self.recovery_time} jours",
            f"Immunité: {self.immunity_duration} jours",
            f"Vaccination: {self.vaccination_rate*100:.0f}% (jour {self.vaccine_start_day})",
        ]

        # Final sayılar
        final_counts = {k: int(self.history[k][-1] * n) for k in states}
        final_text = [
            f"👥 Population: {n}",
            f"🙂 Sains: {final_counts['S']}",
            f"🤒 Infectés: {final_counts['I']}",
            f"💚 Rétablis: {final_counts['R']}",
            f"🟠 Vaccinés: {final_counts['V']}",
            f"🟣 Quarantaine: {final_counts['Q']}",
        ]

        for i, line in enumerate(param_text + final_text):
            ax.text(
                text_x, text_y - i * spacing,
                line,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="top"
            )

        fig.tight_layout()
        fig.savefig(pdf_filename, format="pdf")

        print(f"📄 Simülasyon grafiği + özet PDF olarak kaydedildi: {pdf_filename}")
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
            "immunity_duration": int(self.immunity_slider.get()),
            "vaccination_rate": self.vaccination_slider.get(),
            "vaccine_start_day": int(self.vaccine_day_slider.get()),
        }

        threading.Thread(target=self.run_simulation, kwargs=params, daemon=False).start()

    def run_simulation(
        self,
        infection_prob,
        recovery_time,
        immunity_duration,
        vaccination_rate,
        vaccine_start_day,
    ):
        self.setup_simulation(
            infection_prob,
            recovery_time,
            immunity_duration,
            vaccination_rate,
            vaccine_start_day,
        )
        self.ani = animation.FuncAnimation(
            self.fig, self.update, frames=count(), interval=300, repeat=False
        )
        self.canvas.draw()

    def setup_simulation(
        self,
        infection_prob,
        recovery_time,
        immunity_duration,
        vaccination_rate,
        vaccine_start_day,
    ):
        self.G = custom_graph(n=n, degree_distribution=degree_distribution)
        raw_pos = nx.circular_layout(self.G)
        self.pos = {node: (x * 300, y * 800) for node, (x, y) in raw_pos.items()}
        self.quarantine_edges = {}

        self.color_map = {
            "S": "blue",
            "I": "red",
            "R": "green",
            "V": "orange",
            "Q": "purple",
        }
        self.history = {k: [] for k in self.color_map}

        self.vaccination_rate = vaccination_rate
        self.vaccine_start_day = vaccine_start_day
        self.vaccine_applied = False

        hub_nodes = random.sample(list(self.G.nodes), num_hubs)
        for node in self.G.nodes:
            self.G.nodes[node].update(
                state="S", days_infected=0, days_immune=0, days_in_quarantine=0
            )
            if node not in hub_nodes:
                self.G.add_edge(node, random.choice(hub_nodes))

        patient_zero = random.choice(list(self.G.nodes))
        self.G.nodes[patient_zero]["state"] = "I"

        self.step = 0
        self.infection_prob = infection_prob
        self.recovery_time = recovery_time
        self.immunity_duration = immunity_duration

    def get_colors(self):
        return [
            self.color_map.get(self.G.nodes[n]["state"], "gray") for n in self.G.nodes
        ]

    def update(self, frame):
        self.step += 1

        dynamic_quarantine_rate = calculate_dynamic_quarantine_rate(
            self.G, self.quarantine_rate_max
        )

        new_states = apply_infection(self.G, self.infection_prob)

        if self.step >= self.vaccine_start_day and not self.vaccine_applied:
            applied, num_vaccinated = apply_vaccination(
                self.G,
                self.step,
                self.vaccine_start_day,
                self.vaccination_rate,
            )
            if applied:
                self.vaccine_applied = True
                print(f"Aşı uygulandı. Gün: {self.step}, Kişi sayısı: {num_vaccinated}")

        apply_quarantine(
            self.G,
            dynamic_quarantine_rate,
            self.quarantine_edges,
        )

        if not any(self.G.nodes[n]["state"] == "I" for n in self.G.nodes):
            print(f"Épidémie terminée au jour {frame + 1}")
            if self.ani:
                self.ani.event_source.stop()
                self.save_history_to_csv()
                return
            
        update_states(
            self.G,
            new_states,
            self.recovery_time,
            self.immunity_duration,
            self.quarantine_edges,
        )

        self.ax1.clear()
        nx.draw(
            self.G, self.pos, node_color=self.get_colors(), node_size=20, ax=self.ax1
        )
        self.ax1.set_title(f"Étape {frame + 1}")
        self.ax1.axis("off")

        for key in self.history:
            count = sum(1 for n in self.G.nodes if self.G.nodes[n]["state"] == key) / n
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
