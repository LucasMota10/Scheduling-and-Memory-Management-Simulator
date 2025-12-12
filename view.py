import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
from matplotlib.lines import Line2D

from model import Fifo, Sjf, Round_Robin, EDF, CFS_Sim, Process

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
    return "gray"

def build_gantt(alg,gray_after_deadline: bool = False):
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
            if(gray_after_deadline and p.absolute_deadline!=None and p.absolute_deadline < end ):
                width = p.absolute_deadline - start
                if(width>0):
                    ax.add_patch(patches.Rectangle(
                        (start, y_pos[p.id]), width, 0.8,
                        facecolor=color, edgecolor="black", alpha=0.9
                    ))
                    start += width
                if(width<0):
                    width=0
                color = select_color("deadline")
                width = float(duration) - width


            ax.add_patch(patches.Rectangle(
                (start, y_pos[p.id]), width, 0.8,
                facecolor=color, edgecolor="black", alpha=0.9
            ))

            current_time = end
            if end > max_time:
                max_time = end

        if p.absolute_deadline is not None:
            try:
                dline = p.absolute_deadline

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

    fig.tight_layout()

    legend_elements = [
    Line2D([0], [0], color="green", lw=6, label="Executando"),
    Line2D([0], [0], color="blue", lw=6, label="Esperando"),
    Line2D([0], [0], color="red", lw=6, label="Overhead"),
    Line2D([0], [0], color="grey", lw=6, label="Estouro de deadline"),
    Line2D([0], [0], color="brown", lw=2, linestyle="--", label="Deadline Absoluto"),
]

    ax.legend(handles=legend_elements, loc="upper right")

    return fig

class SimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulador de Escalonamento")
        self.geometry("1300x800")

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

        ttk.Label(params, text="Quantum:").pack(side="left", padx=(0,4))
        self.quantum_var = tk.StringVar(value="2")
        self.quantum_spin = tk.Spinbox(params, from_=1, to=1000, textvariable=self.quantum_var, width=5)
        self.quantum_spin.pack(side="left", padx=(0,15))

        ttk.Label(params, text="Overheat:").pack(side="left", padx=(0,4))
        self.overheat_var = tk.StringVar(value="1")
        self.overheat_spin = tk.Spinbox(params, from_=1, to=1000, textvariable=self.overheat_var, width=5)
        self.overheat_spin.pack(side="left", padx=(0,15))

        ttk.Label(params, text="Disk Cost:").pack(side="left", padx=(0,4))
        self.disk_var = tk.StringVar(value="0")
        self.disk_spin = tk.Spinbox(params, from_=0, to=1000, textvariable=self.disk_var, width=5)
        self.disk_spin.pack(side="left")

        self.gray_deadline_var = tk.BooleanVar(value=True) 
        ttk.Checkbutton(params, text="Cinza depois da deadline", variable=self.gray_deadline_var).pack(side="right", padx=(10,4))

        ttk.Button(top, text="Executar", command=self.run_simulation).pack(side="left", padx=10)

        self.graph_frame = ttk.Frame(self)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=(0,6))

        self.results_container = None
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

        try:
            quantum = int(self.quantum_var.get())
            overheat = int(self.overheat_var.get())
            disk_cost = int(self.disk_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Valores numéricos inválidos.")
            return

        if quantum < 1 or overheat < 1:
            messagebox.showerror("Erro", "Quantum e Overheat devem ser no mínimo 1.")
            return

        procs = load_processes(file)

        alg = self.alg_var.get()

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
        else:
            messagebox.showerror("Erro", f"Algoritmo desconhecido: {alg}")
            return

        executor.execute()

        fig = build_gantt(executor,gray_after_deadline=self.gray_deadline_var.get())

        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
        self.canvas_widget = canvas

        self._show_results(executor)

    def _reconstruct_results(self, executor):    
        rows = []
        for p in executor.finished_process:
            current_time = p.arrival
            starts = []
            for state in p.time_line:
                if state.type == "executing":
                    starts.append(current_time)
                current_time += state.duration

            termino = p.finish_time if getattr(p, "finish_time", -1) != -1 else current_time
            turnaround = termino - p.arrival
            espera = turnaround - getattr(p, "total_time", p.remaining_time if hasattr(p, "remaining_time") else 0)

            if p.absolute_deadline is None:
                d_ok = True
            else:
                try:
                    d_ok = termino <= p.absolute_deadline
                except Exception:
                    d_ok = False

            rows.append({
                "id": p.id,
                "chegada": p.arrival,
                "execucao": getattr(p, "total_time", None),
                "deadline": p.absolute_deadline, 
                "prioridade": getattr(p, "priority", None),
                "inicios": starts,
                "termino": termino,
                "espera": espera,
                "turnaround": turnaround,
                "deadline_ok": d_ok
            })
        return rows

    def _compute_summary(self, executor, rows):
        n = len(rows)
        if n == 0:
            return {
                "avg_wait": 0,
                "avg_turnaround": 0,
                "throughput": 0,
                "idle_percent": 0,
                "total_context_switches": 0,
                "total_time": getattr(executor, "actual_time", 0),
                "finished_count": 0
            }

        total_wait = sum(r["espera"] for r in rows)
        total_turn = sum(r["turnaround"] for r in rows)
        avg_wait = total_wait / n
        avg_turn = total_turn / n

        total_time = max(getattr(executor, "actual_time", 0), max(r["termino"] for r in rows))
        throughput = n / total_time if total_time > 0 else 0
        idle_percent = (getattr(executor, "idle_cpu", 0) / total_time) * 100 if total_time > 0 else 0
        
        overloads = getattr(executor, "overload_count", 0)
        ctx_switches = (overloads + n - 1) if n > 0 else 0

        return {
            "avg_wait": avg_wait,
            "avg_turnaround": avg_turn,
            "throughput": throughput,
            "idle_percent": idle_percent,
            "total_context_switches": ctx_switches,
            "total_time": total_time,
            "finished_count": n
        }

    def _show_results(self, executor):
        if self.results_container:
            self.results_container.destroy()

        self.results_container = ttk.Frame(self)
        self.results_container.pack(fill="both", expand=True, padx=10, pady=(4,10))

        right_container = ttk.Frame(self.results_container)
        right_container.pack(side="right", fill="y", padx=(10, 0))

        canvas = tk.Canvas(right_container, width=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
        
        stats_frame = ttk.Frame(canvas)

        stats_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=stats_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        cols = ("id", "chegada", "execucao", "deadline", "prioridade", "inicios", "termino", "espera", "turnaround", "deadline_ok")
        tree = ttk.Treeview(self.results_container, columns=cols, show="headings", height=7)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center", width=90 if c != "inicios" else 160)

        tree.pack(side="left", fill="both", expand=True)

        rows = self._reconstruct_results(executor)
        summary = self._compute_summary(executor, rows)

        for r in rows:
            starts_str = ",".join(str(int(s)) for s in r["inicios"]) if r["inicios"] else ""
            deadline_val = r["deadline"] if r["deadline"] is not None else ""
            tree.insert("", "end", values=(
                r["id"], r["chegada"], r["execucao"], deadline_val, r["prioridade"],
                starts_str, r["termino"], r["espera"], r["turnaround"], "OK" if r["deadline_ok"] else "ESTOUROU"
            ))

        ttk.Label(stats_frame, text="Resumo Quantitativo", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(stats_frame, text=f"Média espera: {summary['avg_wait']:.2f} u.t.").pack(anchor="w")
        ttk.Label(stats_frame, text=f"Média turnaround: {summary['avg_turnaround']:.2f} u.t.").pack(anchor="w")
        ttk.Label(stats_frame, text=f"Throughput: {summary['throughput']:.3f} proc/u.t.").pack(anchor="w")
        ttk.Label(stats_frame, text=f"% CPU ociosa: {summary['idle_percent']:.2f}%").pack(anchor="w")
        ttk.Label(stats_frame, text=f"Total trocas de contexto: {summary['total_context_switches']}").pack(anchor="w")
        ttk.Label(stats_frame, text=f"Tempo total simulado: {summary['total_time']:.2f} u.t.").pack(anchor="w")
        ttk.Label(stats_frame, text=f"Processos finalizados: {summary['finished_count']}").pack(anchor="w")

if __name__ == "__main__":
    app = SimulatorGUI()
    app.mainloop()