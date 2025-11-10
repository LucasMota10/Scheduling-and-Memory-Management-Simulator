import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class Algorithms:
    def __init__(self,quantum,overheat,disk_cost,process_list):

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
    def __init__(self):
    
    def execute(self):

class Sjf(Algorithms):
     def __init__(self):
    
    def execute(self):

class Round_Robin(Algorithms):
     def __init__(self):
    
    def execute(self):

class EDF(Algorithms):
     def __init__(self):
    
    def execute(self):

class CFS_Sim(Algorithms):
     def __init__(self):
    
    def execute(self):


class Process:
    def __init__(self,id,arrival,total_time,priority,deadline,num_pages):
        self.id = id
        self.arrival = arrival
        self.total_time = total_time
        self.priority = priority
        self.deadline = deadline
        self.num_pages = num_pages

        self.remaining_time = total_time
        self.state = 'novo'

        self.vruntime = 0.0

        self.wait_time = 0
        self.turnaround_time = 0
        self.finish_time = -1

