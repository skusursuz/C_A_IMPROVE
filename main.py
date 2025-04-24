"""
Auteur     : Selim Kusursuz & Necip Atamnia
Université : Université Paris-Saclay
Projet     : Simulation Épidémique
Date       : 2025
"""

# main.py

import tkinter as tk
from simulation import SimulationApp

import threading

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop() 
    root.visualize()