import copy
from abc import ABC, abstractmethod
from typing import List

class TimeLine:
    def __init__(self, duration, type):
        self.duration = duration
        self.type = type # "waiting", "executing", "overhead"

class Process:
    def __init__(self, id, arrival, total_time, priority, deadline, num_pages):
        self.id = id
        self.arrival = arrival
        self.priority = priority
        self.deadline = deadline
        self.num_pages = num_pages

        self.remaining_time = total_time
        self.total_time = total_time
        self.state = 'novo'
        
        # Lista de eventos para o Gantt
        self.time_line = []

        # Atributos de controle de execução
        self.vruntime = 0.0
        self.last_active_time = arrival # Importante para calcular espera incremental

        # Métricas finais
        self.wait_time = 0
        self.turnaround_time = 0
        self.finish_time = -1

class Algorithms(ABC):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        self.quantum = quantum
        self.overheat = overheat
        self.disk_cost = disk_cost
        
        # USO DE DEEPCOPY: 
        # Essencial para garantir que cada execução tenha processos "novos",
        # sem herdar o estado 'finalizado' de simulações anteriores.
        self.process_list = copy.deepcopy(process_list)

        self.finished_process = []
        self.actual_time = 0
        self.idle_cpu = 0
        
    @abstractmethod
    def execute(self):
        pass

class Fifo(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        # Ordena por chegada
        self.ready_queue = sorted(self.process_list, key=lambda p: p.arrival)
        
        while self.ready_queue:
            process = self.ready_queue.pop(0) 

            # Verifica se CPU ficou ociosa até a chegada do processo
            if self.actual_time < process.arrival:
                self.idle_cpu += (process.arrival - self.actual_time)
                self.actual_time = process.arrival
           
            # GANTT: Calcular espera inicial (se houver)
            wait_duration = self.actual_time - process.arrival
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            # Execução
            start_time = self.actual_time
            self.actual_time += process.remaining_time 
            
            # GANTT: Registrar execução
            process.time_line.append(TimeLine(process.remaining_time, "executing"))

            # Finalização
            process.remaining_time = 0
            process.finish_time = self.actual_time
            process.state = 'finalizado'
            process.turnaround_time = process.finish_time - process.arrival
            process.wait_time = wait_duration

            self.finished_process.append(process)
            
        print(f"Simulação FIFO concluída. Tempo total: {self.actual_time}")

class Sjf(Algorithms):  
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        num_total_processes = len(self.process_list)

        while len(self.finished_process) < num_total_processes:
            
            # Filtra processos que já chegaram e não terminaram
            available_processes = [
                p for p in self.process_list 
                if p.arrival <= self.actual_time and p.state != 'finalizado'
            ]

            # Se ninguém chegou ainda, avança o tempo
            if not available_processes:
                unfinished = [p for p in self.process_list if p.state != 'finalizado']
                if unfinished:
                    next_arrival_time = min(p.arrival for p in unfinished)
                    self.idle_cpu += (next_arrival_time - self.actual_time)
                    self.actual_time = next_arrival_time
                else:
                    break 
                continue 
            
            # Lógica SJF: Escolhe o menor Job
            available_processes.sort(key=lambda p: p.remaining_time)
            process = available_processes[0] 
            
            # GANTT: Calcula espera
            # Como é não-preemptivo, espera = tempo atual - chegada
            wait_duration = self.actual_time - process.arrival
            if wait_duration > 0:
                # Limpa timeline anterior para garantir (caso lógica mude) e adiciona espera total
                process.time_line = [] 
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            # Execução
            process.state = 'em execução'
            execution_time = process.remaining_time
            self.actual_time += execution_time
            
            # GANTT: Registrar execução
            process.time_line.append(TimeLine(execution_time, "executing"))
            
            # Finalização
            process.remaining_time = 0
            process.finish_time = self.actual_time
            process.state = 'finalizado'
            
            process.turnaround_time = process.finish_time - process.arrival
            process.wait_time = wait_duration

            self.finished_process.append(process)

        print(f"Simulação SJF concluída. Tempo total: {self.actual_time}")

class Round_Robin(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        num_total_processes = len(self.process_list)
        upcoming_processes = sorted(self.process_list, key=lambda p: p.arrival)
        ready_queue = [] 

        # Inicializa last_active_time para cálculo correto da espera inicial
        for p in self.process_list:
            p.last_active_time = p.arrival

        while len(self.finished_process) < num_total_processes:
            
            # Adiciona novos processos à fila
            newly_arrived = [p for p in upcoming_processes if p.arrival <= self.actual_time]
            for p in newly_arrived:
                ready_queue.append(p)
                upcoming_processes.remove(p)

            if not ready_queue:
                if upcoming_processes:
                    next_arrival = upcoming_processes[0].arrival
                    self.idle_cpu += (next_arrival - self.actual_time)
                    self.actual_time = next_arrival
                else:
                    break 
                continue 
            
            process = ready_queue.pop(0)
            
            # --- GANTT: Espera ---
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))
            
            # --- Execução ---
            time_slice = min(process.remaining_time, self.quantum)
            process.state = 'em execução'
            
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            # --- GANTT: Execução ---
            process.time_line.append(TimeLine(time_slice, "executing"))
            
            # Atualiza tempo ativo (fim da execução)
            process.last_active_time = self.actual_time

            if process.remaining_time == 0:
                # Finaliza
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                # Não acabou: Volta para fila
                process.state = 'pronto'
                
                # --- SOBRECARGA (OVERHEAD) ---
                # Aplica overhead antes de voltar para a fila
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    # Atualiza last_active_time para incluir o overhead 
                    # (para não contar overhead como tempo de espera na próxima vez)
                    process.last_active_time = self.actual_time

                # Adiciona quem chegou durante a execução ou durante o overhead
                newly_arrived_during_run = [p for p in upcoming_processes if p.arrival <= self.actual_time]
                for p in newly_arrived_during_run:
                    ready_queue.append(p)
                    upcoming_processes.remove(p)
                
                ready_queue.append(process)

        print(f"Simulação Round Robin concluída. Tempo total: {self.actual_time}")

class EDF(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        num_total_processes = len(self.process_list)

        # Inicializa o rastreador de tempo ativo para cálculo de espera no Gantt
        for p in self.process_list:
            p.last_active_time = p.arrival

        while len(self.finished_process) < num_total_processes:
            
            # 1. Busca processos que já chegaram (Arrival <= Tempo Atual)
            available_processes = [
                p for p in self.process_list 
                if p.arrival <= self.actual_time and p.state != 'finalizado'
            ]

            # 2. Se a CPU estiver ociosa (ninguém chegou ainda)
            if not available_processes:
                unfinished = [p for p in self.process_list if p.state != 'finalizado']
                if unfinished:
                    # Avança o tempo (idle) até o próximo processo chegar
                    next_arrival_time = min(p.arrival for p in unfinished)
                    self.idle_cpu += (next_arrival_time - self.actual_time)
                    self.actual_time = next_arrival_time
                else:
                    break 
                continue 
            
            # 3. ORDENAÇÃO EDF (Preemptivo): 
            # A cada ciclo, reordena pela Deadline mais próxima.
            # Quem tem menor deadline assume a ponta.
            available_processes.sort(key=lambda p: p.deadline if p.deadline is not None else float('inf'))
            
            process = available_processes[0] 
            
            # --- GANTT: Registro de Espera ---
            # Se passou tempo desde a última vez que ele rodou (ou chegou), conta como espera (barra azul)
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            # --- Execução (Quantum) ---
            # Define quanto tempo vai rodar: O que for menor entre o Quantum e o Tempo Restante
            time_slice = min(process.remaining_time, self.quantum)
            
            process.state = 'em execução'
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            # --- GANTT: Registro de Execução (barra verde) ---
            process.time_line.append(TimeLine(time_slice, "executing"))
            
            # Atualiza o momento que ele parou de executar
            process.last_active_time = self.actual_time

            # --- Verificação de Término ou Troca ---
            if process.remaining_time == 0:
                # Se acabou, finaliza e calcula estatísticas
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                # Se NÃO acabou, volta para a fila de prontos
                process.state = 'pronto'
                
                # APLICAÇÃO DA SOBRECARGA (REGRA SOLICITADA):
                # Como o processo vai voltar para a fila, aplicamos o custo de troca de contexto (Overhead).
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    
                    # --- GANTT: Registro de Overhead (barra vermelha) ---
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    
                    # O tempo de overhead conta como tempo "ocupado" pelo sistema para este processo,
                    # então atualizamos o last_active_time para o fim do overhead.
                    process.last_active_time = self.actual_time

        print(f"Simulação EDF (Preemptivo) concluída. Tempo total: {self.actual_time}")

class CFS_Sim(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        num_total_processes = len(self.process_list)
        upcoming_processes = sorted(self.process_list, key=lambda p: p.arrival)
        ready_rbtree = [] 

        # Inicializa last_active_time
        for p in self.process_list:
            p.last_active_time = p.arrival

        # Avança tempo inicial se necessário
        if upcoming_processes:
            if self.actual_time < upcoming_processes[0].arrival:
                self.actual_time = upcoming_processes[0].arrival
        else:
            return 

        while len(self.finished_process) < num_total_processes:
            
            # Chegada de processos
            newly_arrived = [p for p in upcoming_processes if p.arrival <= self.actual_time]
            for p in newly_arrived:
                # Lógica de vruntime mínimo para novos processos (evita starvation dos antigos)
                if ready_rbtree:
                    min_vruntime = min(proc.vruntime for proc in ready_rbtree)
                    p.vruntime = min_vruntime
                else:
                    p.vruntime = self.actual_time 
                
                ready_rbtree.append(p)
                upcoming_processes.remove(p)

            if not ready_rbtree:
                if upcoming_processes:
                    next_arrival = upcoming_processes[0].arrival
                    self.idle_cpu += (next_arrival - self.actual_time)
                    self.actual_time = next_arrival
                else:
                    break
                continue
            
            # Escolhe processo com menor vruntime
            ready_rbtree.sort(key=lambda p: p.vruntime)
            process = ready_rbtree.pop(0)
            
            # --- GANTT: Espera ---
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))
            
            # --- Execução ---
            time_slice = min(process.remaining_time, self.quantum)
            process.state = 'em execução'
            
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            # Penalidade CFS: vruntime aumenta conforme executa (ponderado pela prioridade)
            process.vruntime += time_slice * process.priority 

            # --- GANTT: Execução ---
            process.time_line.append(TimeLine(time_slice, "executing"))
            process.last_active_time = self.actual_time
            
            if process.remaining_time == 0:
                # Finaliza
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                # Não acabou: Volta para fila (Árvore RB)
                process.state = 'pronto'
                
                # --- SOBRECARGA (OVERHEAD) ---
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    process.last_active_time = self.actual_time

                ready_rbtree.append(process)

        print(f"Simulação CFS concluída. Tempo total: {self.actual_time}")