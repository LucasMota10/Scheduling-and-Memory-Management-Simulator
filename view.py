import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
from matplotlib.lines import Line2D

from model import Fifo, Sjf, Round_Robin, EDF, CFS_Sim, Process

# Carrega os processos do arquivo json
def load_processes(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    processes = []
    for p in raw:
        proc = Process(
            p["id"],
            p["arrival"],
            p["total_time"],
            p["priority"],
            p.get("deadline", None),
            p.get("num_pages", 1)
        )
        processes.append(proc)

    return processes

def select_color(state_type: str) -> str:
    if state_type == "executing":
        return "green"
    if state_type == "waiting":
        return "blue"
    if state_type == "overhead":
        return "red"
    #TODO: fazer com que fique cinza caso passe da deadline
    return "gray"

#Função que monta o gráfico de Gantt
def build_gantt(alg):
    fig = plt.Figure(figsize=(10, 5), dpi=100)
    ax = fig.add_subplot(111)

    y_pos = {}
    y = 0
    for p in alg.finished_process:
        y_pos[p.id] = y
        y += 1

    max_time = 0
    for p in alg.finished_process:
        current_time = p.arrival

        for state in p.time_line:
            duration = state.duration
            stype = state.type

            start = current_time
            width = float(duration)
            end = start + width

            color = select_color(stype)

            ax.add_patch(patches.Rectangle(
                (start, y_pos[p.id]), width, 0.8,
                facecolor=color, edgecolor="black", alpha=0.9
            ))

            current_time = end
            if end > max_time:
                max_time = end

        # desenha linha de deadline se existir
        if p.deadline!=None:
            try:
                dline = p.arrival + int(p.deadline)

                ax.axvline(
                    dline,
                    color="brown",
                    linestyle="--",
                    linewidth=0.8,
                    alpha=0.6
                )

                ax.text(
                    dline + 0.1,           
                    y_pos[p.id] + 0.4,     
                    f"{p.id}",
                    color="black",
                    fontsize=8,
                    rotation=90,
                    va="center"
                )

            except Exception:
                pass

    ticks = [y_pos[k] + 0.4 for k in y_pos.keys()]
    labels = [str(k) for k in y_pos.keys()]
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)

    ax.set_xlim(0, max_time + 1)
    ax.set_xticks(range(0, int(max_time) + 1, 2))
    ax.set_ylim(-0.1, max(0, len(y_pos)) ) 
    ax.set_xlabel("Tempo")
    ax.set_title("Gráfico de Gantt")

    ax.invert_yaxis()
    
    #grid para ajudar vizualização
    #ax.grid(axis="x", color="#000000", linewidth=0.6, linestyle="--")

    fig.tight_layout()

    legend_elements = [
    Line2D([0], [0], color="green", lw=6, label="Executando"),
    Line2D([0], [0], color="blue", lw=6, label="Esperando"),
    Line2D([0], [0], color="red", lw=6, label="Overhead"),
    Line2D([0], [0], color="brown", lw=2, linestyle="--", label="Deadline ID"),
]

    ax.legend(handles=legend_elements, loc="upper right")

    return fig

class SimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulador de Escalonamento")
        self.geometry("1100x700")

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Arquivo JSON:").pack(side="left")
        self.file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.file_var, width=50).pack(side="left", padx=5)
        ttk.Button(top, text="Abrir", command=self.load_file).pack(side="left")

        ttk.Label(top, text="Algoritmo:").pack(side="left", padx=10)
        self.alg_var = tk.StringVar(value="FIFO")
        ttk.Combobox(top, textvariable=self.alg_var,
                     values=["FIFO", "SJF", "Round Robin", "EDF", "CFS"],
                     width=20).pack(side="left")

        params = ttk.Frame(self)
        params.pack(fill="x", padx=10, pady=(0,10))

        # Quantum
        ttk.Label(params, text="Quantum:").pack(side="left", padx=(0,4))
        self.quantum_var = tk.StringVar(value="2")
        self.quantum_spin = tk.Spinbox(params, from_=0, to=1000, textvariable=self.quantum_var, width=5)
        self.quantum_spin.pack(side="left", padx=(0,15))

        # Overheat
        ttk.Label(params, text="Overheat:").pack(side="left", padx=(0,4))
        self.overheat_var = tk.StringVar(value="1")
        self.overheat_spin = tk.Spinbox(params, from_=0, to=1000, textvariable=self.overheat_var, width=5)
        self.overheat_spin.pack(side="left", padx=(0,15))

        # Disk Cost
        ttk.Label(params, text="Disk Cost:").pack(side="left", padx=(0,4))
        self.disk_var = tk.StringVar(value="0")
        self.disk_spin = tk.Spinbox(params, from_=0, to=1000, textvariable=self.disk_var, width=5)
        self.disk_spin.pack(side="left")


        ttk.Button(top, text="Executar", command=self.run_simulation).pack(side="left", padx=10)

        self.graph_frame = ttk.Frame(self)
        self.graph_frame.pack(fill="both", expand=True)

        self.canvas_widget = None

    def load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")]
        )
        if path:
            self.file_var.set(path)

    def run_simulation(self):
        file = self.file_var.get()
        if not file:
            messagebox.showerror("Erro", "Selecione um arquivo JSON.")
            return

        procs = load_processes(file)

        alg = self.alg_var.get()

        quantum = int(self.quantum_var.get())
        overheat =int(self.overheat_var.get())
        disk_cost = int(self.disk_var.get())

        if alg == "FIFO":
            executor = Fifo(quantum, overheat, disk_cost, procs)
        elif alg == "SJF":
            executor = Sjf(quantum, overheat, disk_cost, procs)
        elif alg == "Round Robin":
            executor = Round_Robin(quantum, overheat, disk_cost, procs)
        elif alg == "EDF":
            executor = EDF(quantum, overheat, disk_cost, procs)
        elif alg == "CFS":
            executor = CFS_Sim(quantum, overheat, disk_cost, procs)

        executor.execute()

        fig = build_gantt(executor)

        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.canvas_widget = canvas

if __name__ == "__main__":
    app = SimulatorGUI()
    app.mainloop()
