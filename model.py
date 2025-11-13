import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List
class Process:
    def __init__(self,id,arrival,total_time,priority,deadline,num_pages):
        self.id = id
        self.arrival = arrival
        self.priority = priority
        self.deadline = deadline
        self.num_pages = num_pages

        self.remaining_time = total_time
        self.state = 'novo'

        self.vruntime = 0.0

        self.wait_time = 0
        self.turnaround_time = 0
        self.finish_time = -1
class Algorithms:
    def __init__(self,quantum: int,overheat: int,disk_cost: int,process_list: list[Process]):

        self.quantum = quantum
        self.overheat = overheat
        self.disk_cost = disk_cost
        self.process_list = process_list

        self.ready_queue = sorted(process_list, key=lambda p: p.arrival)

        self.blocked_queue = []
        self.finished_process = []

        self.actual_time = 0
        self.actual_process = None
        self.idle_cpu = 0
        
        self.log = []

    @abstractmethod
    def execute(self):
        pass

class Fifo(Algorithms):
  
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List['Process']):
    
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:

        self.ready_queue = sorted(self.process_list, key=lambda p: p.arrival)
        
        while self.ready_queue:
            process = self.ready_queue.pop(0) 

            if self.actual_time < process.arrival:
                self.idle_cpu += (process.arrival - self.actual_time)
                self.actual_time = process.arrival
           
            start_time = self.actual_time
            
            self.actual_time += process.remaining_time 
            
            process.remaining_time = 0
            process.finish_time = self.actual_time
            process.state = 'finalizado'

            process.turnaround_time = process.finish_time - process.arrival

            process.wait_time = start_time - process.arrival

            self.finished_process.append(process)
            
        print("Simulação FIFO concluída. Tempo total de CPU:", self.actual_time)
class Sjf(Algorithms):
    def __init__(self, quantum: int, overheat: int, disk_cost: int, process_list: List['Process']):
        super().__init__(quantum, overheat, disk_cost, process_list)

    def execute(self) -> None:
        
        num_total_processes = len(self.process_list)

        while len(self.finished_process) < num_total_processes:
            
            available_processes = [
                p for p in self.process_list 
                if p.arrival <= self.actual_time and p.state != 'finalizado'
            ]

            if not available_processes:
                try:
                    next_arrival_time = min(
                        p.arrival for p in self.process_list if p.state == 'novo'
                    )
                    self.idle_cpu += (next_arrival_time - self.actual_time)
                    self.actual_time = next_arrival_time
                except ValueError:
                    break 
                
                continue 
            
            available_processes.sort(key=lambda p: p.remaining_time)
            
            process = available_processes[0] 
            
            process.state = 'em execução'
            start_time = self.actual_time
            
            self.actual_time += process.remaining_time
            
            process.remaining_time = 0
            process.finish_time = self.actual_time
            process.state = 'finalizado'
            
            process.turnaround_time = process.finish_time - process.arrival
            
            process.wait_time = start_time - process.arrival

            self.finished_process.append(process)

        print(f"Simulação SJF concluída. Tempo total: {self.actual_time}")

class Round_Robin(Algorithms):
     def __init__(self):
    
    def execute(self):

class EDF(Algorithms):
     def __init__(self):
    
    def execute(self):

class CFS_Sim(Algorithms):
     def __init__(self):
    
    def execute(self):




