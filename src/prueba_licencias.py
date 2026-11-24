"""Iteracion 0: verifica que Gurobi y CPLEX tengan licencia COMPLETA.

Arma una mochila con 3.000 variables binarias: la licencia limitada de Gurobi
(2.000 vars) y CPLEX Community Edition (1.000 vars) fallan con este tamano.

Uso:  python src/prueba_licencias.py
"""
import random
import time

N = 3000
random.seed(1)
v = [random.randint(1, 100) for _ in range(N)]
p = [random.randint(1, 100) for _ in range(N)]
C = sum(p) // 3


def probar_gurobi():
    import gurobipy as gp
    from gurobipy import GRB
    m = gp.Model("prueba")
    m.Params.OutputFlag = 0
    m.Params.TimeLimit = 30
    x = m.addVars(N, vtype=GRB.BINARY)
    m.addConstr(gp.quicksum(p[i] * x[i] for i in range(N)) <= C)
    m.setObjective(gp.quicksum(v[i] * x[i] for i in range(N)), GRB.MAXIMIZE)
    m.optimize()
    return f"gurobipy {gp.gurobi.version()} | obj={m.ObjVal:.0f} | gap={100*m.MIPGap:.4f}%"


def probar_cplex():
    from docplex.mp.model import Model
    m = Model("prueba")
    m.set_time_limit(30)
    x = m.binary_var_list(N)
    m.add_constraint(m.sum(p[i] * x[i] for i in range(N)) <= C)
    m.maximize(m.sum(v[i] * x[i] for i in range(N)))
    s = m.solve()
    if s is None:
        raise RuntimeError(m.solve_details.status)
    gap = m.solve_details.mip_relative_gap
    return f"CPLEX {m.get_cplex().get_version()} | obj={s.objective_value:.0f} | gap={100*gap:.4f}%"


for nombre, f in (("Gurobi", probar_gurobi), ("CPLEX", probar_cplex)):
    t = time.time()
    try:
        print(f"[OK]    {nombre}: {f()}  ({time.time()-t:.1f} s)")
    except Exception as e:
        print(f"[FALLA] {nombre}: {type(e).__name__}: {e}")
print("\nSi ambos dicen OK con el mismo obj, la iteracion 0 de licencias esta lista.")
