import sys
import os
import time
from ortools.sat.python import cp_model

def main():
    start_time = time.time()
    
    if len(sys.argv) != 4:
        print("Usage: python solver.py <mode: E|H> <input_file> <output_file>")
        sys.exit(1)

    mode, input_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]

    if mode != "E" and mode != "H":
        print("Invalid mode. Use 'E' for exact or 'H' for heuristic.")
        sys.exit(1)
    
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    try:
        with open(output_file, 'w') as f:
            pass
    except IOError:
        print(f"Error: Cannot write to output file '{output_file}'.")
        sys.exit(1)

    for line in open(input_file, 'r'):
        if line.startswith('c'):
            continue
        if line.startswith('p'):
            _, problem, n, m = line.strip().split()
            n = int(n)
            m = int(m)
            if problem == 'ds':
                edges = []
            elif problem == 'hs':
                sets = set()
            if problem != 'ds' and problem != 'hs':
                print(f"Error: Invalid input file '{input_file}'.")
                sys.exit(1)
            continue
        if problem == 'ds':
            u, v = map(int, line.strip().split())
            edges.append([u, v])
            m -= 1
            if m == 0:
                break
        else:
            temp=[]
            for i in map(int, line.strip().split()):
                temp.append(i - 1)
            sets.add(frozenset(temp))
            m -= 1
            if m == 0:
                break
    
    if problem == 'ds':
        sets=[[] for i in range(n)]
        for i in range(len(edges)):
            sets[edges[i][0] - 1].append(edges[i][1] - 1)
            sets[edges[i][1] - 1].append(edges[i][0] - 1)
        for i in range(n):
            sets[i].append(i)
        sets={frozenset(x) for x in sets}
    
    model = cp_model.CpModel()
    vbin=[model.NewBoolVar('') for i in range(n)]
    model.Minimize(sum(vbin))
    for fs in sets:
        model.AddBoolOr(vbin[i] for i in fs)
    
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    solver.parameters.num_search_workers = 1
    
    done = False
    if mode == "H":
        solver.parameters.max_time_in_seconds = 5*60.0 - 10 - (time.time() - start_time)
        solver.parameters.subsolvers.append("less_encoding")
        solver.parameters.ignore_subsolvers.append("ls")
        solver.parameters.optimize_with_core = True
    
    else:
        if problem == "hs":
            solver.parameters.max_time_in_seconds = 15*60.0 - 10 - (time.time() - start_time)
            solver.parameters.subsolvers.append("pseudo_costs")
            status = solver.Solve(model)
            
            if status == cp_model.OPTIMAL:
                done = True
            
            for i in range(n):
                model.AddHint(vbin[i],solver.Value(vbin[i]))
        
        solver.parameters.max_time_in_seconds = 30*60.0 - 10 - (time.time() - start_time)
        solver.parameters.optimize_with_core = True
        solver.parameters.subsolvers.append("no_lp")
        
        if problem == "ds":
            solver.parameters.binary_minimization_algorithm=4
            solver.parameters.minimization_algorithm=2
            solver.parameters.max_sat_reverse_assumption_order=True
    
    if not done:
        status = solver.Solve(model)
    
    with open(output_file, 'w') as f:
        f.write(f"{int(solver.ObjectiveValue())}\n")
        for i in range(len(vbin)):
            if solver.Value(vbin[i]) >= 0.5:
                f.write(f"{i + 1}\n")

if __name__ == "__main__":
    main()
