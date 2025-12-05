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
        self.num_pages = num_pages

        # LÓGICA DE DEADLINE ALTERADA:
        # O deadline informado é relativo (duração).
        # O deadline absoluto é a Chegada + Duração.
        self.deadline_duration = deadline 
        if deadline is not None:
            self.absolute_deadline = arrival + deadline
        else:
            self.absolute_deadline = None

        self.remaining_time = total_time
        self.total_time = total_time
        self.state = 'novo'
        
        # Lista de eventos para o Gantt
        self.time_line = []

        # Atributos de controle de execução
        self.vruntime = 0.0
        self.last_active_time = arrival 

        # Métricas finais
        self.wait_time = 0
        self.turnaround_time = 0
        self.finish_time = -1

class Algorithms(ABC):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        self.quantum = quantum
        self.overheat = overheat
        self.disk_cost = disk_cost
        
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
        self.ready_queue = sorted(self.process_list, key=lambda p: p.arrival)
        
        while self.ready_queue:
            process = self.ready_queue.pop(0) 

            if self.actual_time < process.arrival:
                self.idle_cpu += (process.arrival - self.actual_time)
                self.actual_time = process.arrival
           
            wait_duration = self.actual_time - process.arrival
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            start_time = self.actual_time
            self.actual_time += process.remaining_time 
            
            process.time_line.append(TimeLine(process.remaining_time, "executing"))

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
            available_processes = [
                p for p in self.process_list 
                if p.arrival <= self.actual_time and p.state != 'finalizado'
            ]

            if not available_processes:
                unfinished = [p for p in self.process_list if p.state != 'finalizado']
                if unfinished:
                    next_arrival_time = min(p.arrival for p in unfinished)
                    self.idle_cpu += (next_arrival_time - self.actual_time)
                    self.actual_time = next_arrival_time
                else:
                    break 
                continue 
            
            available_processes.sort(key=lambda p: p.remaining_time)
            process = available_processes[0] 
            
            wait_duration = self.actual_time - process.arrival
            if wait_duration > 0:
                process.time_line = [] 
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            process.state = 'em execução'
            execution_time = process.remaining_time
            self.actual_time += execution_time
            
            process.time_line.append(TimeLine(execution_time, "executing"))
            
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

        for p in self.process_list:
            p.last_active_time = p.arrival

        while len(self.finished_process) < num_total_processes:
            
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
            
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))
            
            time_slice = min(process.remaining_time, self.quantum)
            process.state = 'em execução'
            
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            process.time_line.append(TimeLine(time_slice, "executing"))
            process.last_active_time = self.actual_time

            if process.remaining_time == 0:
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                process.state = 'pronto'
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    process.last_active_time = self.actual_time

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

        for p in self.process_list:
            p.last_active_time = p.arrival

        while len(self.finished_process) < num_total_processes:
            
            available_processes = [
                p for p in self.process_list 
                if p.arrival <= self.actual_time and p.state != 'finalizado'
            ]

            if not available_processes:
                unfinished = [p for p in self.process_list if p.state != 'finalizado']
                if unfinished:
                    next_arrival_time = min(p.arrival for p in unfinished)
                    self.idle_cpu += (next_arrival_time - self.actual_time)
                    self.actual_time = next_arrival_time
                else:
                    break 
                continue 
            
            # ALTERAÇÃO NO EDF: Ordena pelo Absolute Deadline (Chegada + Duração)
            # Se não tiver deadline, vai para o final da fila (inf)
            available_processes.sort(key=lambda p: p.absolute_deadline if p.absolute_deadline is not None else float('inf'))
            
            process = available_processes[0] 
            
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))

            time_slice = min(process.remaining_time, self.quantum)
            
            process.state = 'em execução'
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            process.time_line.append(TimeLine(time_slice, "executing"))
            process.last_active_time = self.actual_time

            if process.remaining_time == 0:
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                process.state = 'pronto'
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    process.last_active_time = self.actual_time

        print(f"Simulação EDF (Preemptivo) concluída. Tempo total: {self.actual_time}")

class CFS_Sim(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List[Process]):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        num_total_processes = len(self.process_list)
        upcoming_processes = sorted(self.process_list, key=lambda p: p.arrival)
        ready_rbtree = [] 

        for p in self.process_list:
            p.last_active_time = p.arrival

        if upcoming_processes:
            if self.actual_time < upcoming_processes[0].arrival:
                self.actual_time = upcoming_processes[0].arrival
        else:
            return 

        while len(self.finished_process) < num_total_processes:
            
            newly_arrived = [p for p in upcoming_processes if p.arrival <= self.actual_time]
            for p in newly_arrived:
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
            
            ready_rbtree.sort(key=lambda p: p.vruntime)
            process = ready_rbtree.pop(0)
            
            wait_duration = self.actual_time - process.last_active_time
            if wait_duration > 0:
                process.time_line.append(TimeLine(wait_duration, "waiting"))
            
            time_slice = min(process.remaining_time, self.quantum)
            process.state = 'em execução'
            
            self.actual_time += time_slice
            process.remaining_time -= time_slice
            
            process.vruntime += time_slice * process.priority 

            process.time_line.append(TimeLine(time_slice, "executing"))
            process.last_active_time = self.actual_time
            
            if process.remaining_time == 0:
                process.state = 'finalizado'
                process.finish_time = self.actual_time
                process.turnaround_time = process.finish_time - process.arrival
                process.wait_time = process.turnaround_time - process.total_time
                self.finished_process.append(process)
            else:
                process.state = 'pronto'
                if self.overheat > 0:
                    self.actual_time += self.overheat
                    process.time_line.append(TimeLine(self.overheat, "overhead"))
                    process.last_active_time = self.actual_time

                ready_rbtree.append(process)

        print(f"Simulação CFS concluída. Tempo total: {self.actual_time}")