"""
Auteur     : Selim Kusursuz & Necip Atamnia
Université : Université Paris-Saclay
Projet     : Simulation Épidémique
Date       : 2025
"""

# utils.py

from tkinter import ttk
import tkinter as tk
import threading


def create_slider(parent, label, min_val, max_val, init_val, row):
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")

    # Değeri göstermek için StringVar ve Label
    value_var = tk.StringVar()
    value_var.set(f"{init_val:.2f}")

    def on_slide(val):
        value_var.set(f"{float(val):.2f}")  # Slider değeri değiştikçe güncelle

    slider = ttk.Scale(
        parent,
        from_=min_val,
        to=max_val,
        value=init_val,
        length=200,
        orient="horizontal",
        command=on_slide
    )
    slider.grid(row=row, column=1)

    value_label = ttk.Label(parent, textvariable=value_var, width=5)
    value_label.grid(row=row, column=2, padx=5)

    return slider

