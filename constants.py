"""
Auteur     : Selim Kusursuz & Necip Atamnia
Université : Université Paris-Saclay
Projet     : Simulation Épidémique
Date       : 2025
"""


# constants.py

n = 150
p_edge = 0.3
quarantine_rate = 0.02
num_hubs = 20


SLIDER_CONFIGS = [
    {
        "label": "Taux d'infection",
        "from_": 0.01,
        "to": 3.0,
        "default": 0.1,
        "row": 0,
        "attr": "infection_slider",
    },
    {
        "label": "Temps de guérison",
        "from_": 1,
        "to": 20,
        "default": 8,
        "row": 1,
        "attr": "recovery_slider",
    },
    {
        "label": "Durée d'immunité",
        "from_": 10,
        "to": 50,
        "default": 20,
        "row": 2,
        "attr": "immunity_slider",
    },
    {
        "label": "Taux de vaccination",
        "from_": 0.0,
        "to": 0.5,
        "default": 0.01,
        "row": 3,
        "attr": "vaccination_slider",
    },
    {
        "label": "Jour de début du vaccin",
        "from_": 0,
        "to": 100,
        "default": 20,
        "row": 4,
        "attr": "vaccine_day_slider",
    },
    {
        "label": "Taux de quarantaine (max)",
        "from_": 0.0,
        "to": 1.0,
        "default": 0.05,
        "row": 5,
        "attr": "quarantine_slider",
    },
]

# Preset parametreleri
PRESETS = {
    "COVID-19": {
        "infection_slider": 0.2,
        "recovery_slider": 10,
        "immunity_slider": 90,
        "vaccination_slider": 0.7,
        "vaccine_day_slider": 20,
    },
    "Grippe espagnole": {
        "infection_slider": 0.3,
        "recovery_slider": 10,
        "immunity_slider": 90,
        "vaccination_slider": 0.0,
        "vaccine_day_slider": 20,
    },
}
