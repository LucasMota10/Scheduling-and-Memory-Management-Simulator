import pandas as pd
import numpy as np

class simulator:
    def __init__(self,quantum,overheat,disk_cost,processos):

        self.quantum = quantum
        self.overheat = overheat
        self.disk_cost = disk_cost
        self.processos = processos

        self.processos_futuros = sorted(processos, key=lambda p: p.arrival)
        self.ready_queue = []
        self.blocked_queue = []
        self.finished_process = []

        self.actual_time = 0
        self.actual_process = None
        self.idle_cpu = 0
        self.pre_emption = 0

        self.log = []
class process:
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