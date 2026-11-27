"""Modelo PLE de CB-CTT (ITC-2007 track 3) en Gurobi: restricciones duras + blandas.

VARIABLES
  x[c,r,t] binaria  1 si una clase del curso c se dicta en la sala r en el slot t
  y[c,d]   binaria  1 si el curso c tiene clase el dia d
  w[c]     >= 0     dias que le faltan al curso c para llegar a su minimo
  u[c]     binaria  1 si al curso c le faltan dias (w > 0)
  v[c,r]   binaria  1 si el curso c usa la sala r alguna vez
  e[g,t]   >= 0     1 si el curriculo g tiene una clase aislada en el slot t

DURAS
  (1) sum_{r,t} x[c,r,t] = l_c                         todo curso c
  (2) sum_c x[c,r,t] <= 1                              toda sala r, slot t
  (3) sum_{c in G} sum_r x[c,r,t] <= 1                 todo slot t y todo G =
                                                       un curso, un curriculo o un profesor
  (4) x[c,r,t] no existe si c no puede dictarse en t   (disponibilidad)

BLANDAS (pesos ITC-2007)
  (5) y[c,d] <= sum_{r, t en d} x[c,r,t]               dias usados: y = 1 exactamente
      y[c,d] >= sum_r x[c,r,t]   para todo t en d      cuando c tiene clase el dia d
  (6) w[c] >= mnd_c - n_c,   w[c] <= mnd_c * u[c],     dias minimos, con n_c = sum_d y[c,d]:
      w[c] <= mnd_c - n_c + mnd_c * (1 - u[c])         w = max(0, mnd_c - n_c) exactamente
  (7) e[q,t] >= z[q,t] - sum_{s vecino de t} z[q,s]    compacidad, con
      e[q,t] <= z[q,t],  e[q,t] <= 1 - z[q,s]          z[q,t] = sum_{c in q} sum_r x[c,r,t] (0/1 por (3));
                                                       e = 1 exactamente si la clase esta aislada
  (8) x[c,r,t] <= v[c,r] <= sum_t x[c,r,t]             estabilidad de sala: v = 1 exactamente si c usa r

  Las cotas superiores de (5)-(8) no cambian el optimo, pero hacen que el objetivo de CUALQUIER
  solucion entera (no solo la optima) sea igual a su costo real. Sin ellas, una solucion
  incumbente podia reportar penalizaciones que no existian (comp05 con CPLEX: 196.211 vs 8.150 real).

  min  1 * sum exceso[c,r] * x[c,r,t]                  capacidad
     + 5 * sum w[c]
     + 2 * sum e[q,t]
     + 1 * sum_c (sum_r v[c,r] - 1)

Uso (desde la raiz del repo):
    python src/modelo_gurobi.py instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4
    python src/modelo_gurobi.py instancias/itc2007/comp01.ctt --solo-duras     (iteracion 1)
"""
import argparse
import time
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from comun import (PESO_CAPACIDAD, PESO_COMPACIDAD, PESO_DIAS, PESO_ESTABILIDAD,
                   guardar_solucion, preparar, ruta_log)
from leer_ctt import leer_ctt


def construir_modelo(inst, nombre="cbctt", solo_duras=False):
    S = preparar(inst)
    C, R, D, T = S["C"], S["R"], S["D"], S["T"]
    m = gp.Model(nombre)

    x = m.addVars(S["X"], vtype=GRB.BINARY, name="x")

    # ---------------- duras ----------------
    m.addConstrs((x.sum(c, "*", "*") == inst["cursos"][c]["clases"] for c in C), name="clases")
    # (solo para pares (r,t) / (c,t) que tienen variables, igual que en modelo_cplex.py)
    pares_rt = sorted({(r, t) for (_, r, t) in S["X"]})
    pares_ct = sorted({(c, t) for (c, _, t) in S["X"]})
    m.addConstrs((x.sum("*", r, t) <= 1 for (r, t) in pares_rt), name="sala")
    m.addConstrs((x.sum(c, "*", t) <= 1 for (c, t) in pares_ct), name="curso_slot")
    for g, cursos_g in S["grupos"].items():
        for t in T:
            m.addConstr(gp.quicksum(x.sum(c, "*", t) for c in cursos_g) <= 1, name=f"conflicto[{g},{t}]")

    if solo_duras:
        m.setObjective(0, GRB.MINIMIZE)
        m.update()
        return m, x

    # ---------------- blandas ----------------
    # capacidad
    f_capacidad = gp.quicksum(S["exceso"][c, r] * x[c, r, t] for (c, r, t) in S["X"] if S["exceso"][c, r] > 0)

    # dias minimos
    y = m.addVars(C, D, vtype=GRB.BINARY, name="y")
    w = m.addVars(C, lb=0, name="w")
    u = m.addVars(C, vtype=GRB.BINARY, name="u")
    m.addConstrs((y[c, d] <= gp.quicksum(x.sum(c, "*", t) for t in S["slots_dia"][d]) for c in C for d in D),
                 name="dia_usado")
    m.addConstrs((y[c, d] >= x.sum(c, "*", t) for c in C for d in D for t in S["slots_dia"][d]),
                 name="dia_usado_inf")
    for c in C:
        mnd = inst["cursos"][c]["min_dias"]
        n_c = y.sum(c, "*")
        m.addConstr(w[c] >= mnd - n_c, name=f"dias_min[{c}]")
        m.addConstr(w[c] <= mnd * u[c], name=f"dias_min_u[{c}]")
        m.addConstr(w[c] <= mnd - n_c + mnd * (1 - u[c]), name=f"dias_min_sup[{c}]")

    # compacidad (solo curriculos)
    curriculos = inst["curriculos"]
    z = {(q, t): gp.quicksum(x.sum(c, "*", t) for c in cs) for q, cs in curriculos.items() for t in T}
    e = m.addVars(list(curriculos), T, lb=0, name="e")
    m.addConstrs((e[q, t] >= z[q, t] - gp.quicksum(z[q, s] for s in S["vecinos"][t])
                  for q in curriculos for t in T), name="aislada")
    m.addConstrs((e[q, t] <= z[q, t] for q in curriculos for t in T), name="aislada_sup")
    m.addConstrs((e[q, t] <= 1 - z[q, s] for q in curriculos for t in T for s in S["vecinos"][t]),
                 name="aislada_vecino")

    # estabilidad de sala
    v = m.addVars(C, R, vtype=GRB.BINARY, name="v")
    m.addConstrs((x[c, r, t] <= v[c, r] for (c, r, t) in S["X"]), name="usa_sala")
    m.addConstrs((v[c, r] <= x.sum(c, r, "*") for c in C for r in R), name="usa_sala_sup")

    m.setObjective(PESO_CAPACIDAD * f_capacidad
                   + PESO_DIAS * w.sum()
                   + PESO_COMPACIDAD * e.sum()
                   + PESO_ESTABILIDAD * (v.sum() - len(C)),
                   GRB.MINIMIZE)
    m.update()
    return m, x


ESTADOS = {GRB.OPTIMAL: "OPTIMO", GRB.TIME_LIMIT: "LIMITE_TIEMPO", GRB.INFEASIBLE: "INFACTIBLE",
           GRB.INF_OR_UNBD: "INFACTIBLE", GRB.INTERRUPTED: "INTERRUMPIDO"}


def resolver(inst, nombre, tiempo, hilos, gap=0.0, solo_duras=False, mostrar=True):
    """Arma y resuelve el modelo. Devuelve un diccionario con los resultados (lo usa src/correr.py)."""
    t0 = time.time()
    m, x = construir_modelo(inst, nombre, solo_duras)
    t_modelo = time.time() - t0
    m.Params.OutputFlag = 1 if mostrar else 0
    m.Params.TimeLimit = tiempo
    m.Params.Threads = hilos
    m.Params.MIPGap = gap
    m.Params.LogFile = str(ruta_log(nombre, "gurobi"))
    if mostrar:
        print(f"{nombre}: {m.NumVars} variables, {m.NumConstrs} restricciones")

    t0 = time.time()
    m.optimize()
    seg = time.time() - t0

    hay_sol = m.SolCount > 0
    estado = ESTADOS.get(m.Status, f"STATUS_{m.Status}")
    if estado == "LIMITE_TIEMPO" and not hay_sol:
        estado = "SIN_SOLUCION"
    sol = []
    if hay_sol:
        P = inst["Periods_per_day"]
        sol = [(c, r, t // P, t % P) for (c, r, t), var in x.items() if var.X > 0.5]
    return {
        "solver": "gurobi",
        "version": ".".join(map(str, gp.gurobi.version())),
        "estado": estado,
        "tiempo_s": seg,
        "tiempo_modelo_s": t_modelo,
        "objetivo": m.ObjVal if hay_sol else None,
        "cota": m.ObjBound if m.Status != GRB.INFEASIBLE else None,
        "gap": m.MIPGap if hay_sol else None,
        "nodos": int(m.NodeCount),
        "variables": m.NumVars,
        "restricciones": m.NumConstrs,
        "solucion": sol,
    }


def main():
    ap = argparse.ArgumentParser(description="CB-CTT en Gurobi")
    ap.add_argument("instancia", help="ruta al archivo .ctt")
    ap.add_argument("--tiempo", type=float, default=60, help="limite de tiempo en segundos")
    ap.add_argument("--hilos", type=int, default=4, help="Threads (usar el mismo en CPLEX)")
    ap.add_argument("--gap", type=float, default=0.0, help="MIPGap relativo (0 = demostrar optimo)")
    ap.add_argument("--solo-duras", action="store_true", help="sin restricciones blandas (iteracion 1)")
    args = ap.parse_args()

    inst = leer_ctt(args.instancia)
    nombre = Path(args.instancia).stem
    r = resolver(inst, nombre, args.tiempo, args.hilos, args.gap, args.solo_duras)
    if not r["solucion"]:
        print(f"\n{nombre} [gurobi]: {r['estado']} en {r['tiempo_s']:.1f} s")
        return
    ruta = guardar_solucion(r["solucion"], nombre, "gurobi")
    print(f"\n{nombre} [gurobi]  estado={r['estado']}  objetivo={r['objetivo']:.0f}  cota={r['cota']:.2f}  "
          f"gap={100 * r['gap']:.2f}%  tiempo={r['tiempo_s']:.1f}s")
    print(f"Revisala con:  python src/verificar.py {args.instancia} {ruta.relative_to(ruta.parents[2]).as_posix()}")

if __name__ == "__main__":
    main()
