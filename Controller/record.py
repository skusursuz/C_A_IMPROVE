from datetime import datetime
import csv
import matplotlib.pyplot as plt
from Model.Params.constants import n

def save_history_to_csv(self, filename=None):
        """
        Enregistre les données de la simulation dans un fichier CSV
        et sauvegarde le graphique + résumé sous forme de fichier PDF.
        """
        if filename is None:
            today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{today}_simulation_result.csv"

        pdf_filename = filename.replace(".csv", ".pdf")

        # Garder l'ordre des états constant.
        states = ["S", "I", "R", "V", "Q"]

        try:
            steps = len(next(iter(self.history.values())))
        except (StopIteration, TypeError):
            print("Aucune donnée d’historique à enregistrer.")
            return

        # === ENREGISTREMENT CSV ===
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Temps"] + states)
            for i in range(steps):
                row = [i] + [self.history.get(state, [0]*steps)[i] for state in states]
                writer.writerow(row)

        print(f"Historique de la simulation enregistré au format CSV : {filename}")

        # === GRAPHIQUE + TEXTE EN PDF ===
        fig, ax = plt.subplots(figsize=(10, 6))

        # Tracer les courbes
        for state in states:
            ax.plot(self.history[state], label=state)

        ax.set_title("Évolution des états dans la population")
        ax.set_xlabel("Temps (jours)")
        ax.set_ylabel("Proportion")
        ax.set_ylim(0, 1)
        ax.legend()

        # TEXTE : Paramètres
        text_x = 1.02
        text_y = 0.9
        spacing = 0.06

        param_text = [
            f"Durée totale : {self.step} jours",
            f"Taux d'infection : {self.infection_prob:.2f}",
            f"Temps de rétablissement : {self.recovery_time} jours",
            f"Taux de vaccination : {self.vaccination_rate*100:.0f}% (à partir du jour {self.vaccine_start_day})",
        ]

        # Comptes finaux
        final_counts = {k: int(self.history[k][-1] * n) for k in states}
        final_text = [
            f"Population totale : {n}",
            f"Sains : {final_counts['S']}",
            f"Infectés : {final_counts['I']}",
            f"Rétablis : {final_counts['R']}",
            f"Vaccinés : {final_counts['V']}",
            f"En quarantaine : {final_counts['Q']}",
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

        print(f"Graphique et résumé sauvegardés en PDF : {pdf_filename}")
