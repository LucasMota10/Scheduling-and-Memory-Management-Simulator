import argparse
import uuid
import json
import os
from datetime import datetime
from model import Process

FILE = "processes.json"

def load_processes():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Gerencia nomes")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # subcomand “add”
    parser_add = subparsers.add_parser("add", help="add a process")
    parser_add.add_argument("name", help="name of process")
    parser_add.add_argument("--duration", default=1, type=int, help="duration of process")
    parser_add.add_argument("--priority", default=1, type=int, help="priority of process")
    parser_add.add_argument("--deadline", default=None, type=int, help="deadline of process")
    parser_add.add_argument("--pages", default=1, type=int, help="number of pages of process")
    parser_add.add_argument("--arrival", default=1, type=int, help="arrival of process")

    # subcomand “list”
    parser_list = subparsers.add_parser("list", help="List all process")

    args = parser.parse_args()

    if args.comando == "add":
        p = Process(args.name, args.arrival, args.duration, args.priority, args.deadline, args.pages)

        processes = load_processes()
        processes.append(p.__dict__)      

        with open(FILE, "w") as f:
            json.dump(processes, f, indent=4)
        print(f"Process {args.name} created")
        
    elif args.comando == "list":
        processes = load_processes()
        if not processes:
            print("No processes found.")
            return
        for i, proc in enumerate(processes, start=1):
            print(f"{i}. id={proc.get('id')} arrival={proc.get('arrival')} remaining={proc.get('remaining_time')} priority={proc.get('priority')} pages={proc.get('num_pages')} state={proc.get('state')}")

if __name__ == "__main__":
    main()
