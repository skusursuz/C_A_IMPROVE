"""
Auteur     : Selim Kusursuz & Necip Atamnia
Université : Université Paris-Saclay
Projet     : Simulation Épidémique
Date       : 2025
"""

# main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from Model.simulation import SimulationApp

import threading

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop() 
    root.visualize()