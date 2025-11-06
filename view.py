import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AppGUI:
    def __init__(self):
        self.root = tk.Tk("Escalonador")
