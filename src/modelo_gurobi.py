"""Iteracion 1: modelo PLE con RESTRICCIONES DURAS de CB-CTT (ITC-2007 track 3) en Gurobi.

Variable:  x[c,r,t] = 1 si una clase del curso c se dicta en la sala r en el slot t
           (slot t = dia * periodos_por_dia + periodo).

Restricciones duras:
  (1) Clases:          sum_{r,t} x[c,r,t] = l_c                     para todo curso c
  (2) Ocupacion sala:  sum_c x[c,r,t] <= 1                          para toda sala r, slot t
  (3) Conflictos:      a lo mas una clase por slot de
                       (3a) un mismo curso, (3b) un mismo curriculo, (3c) un mismo profesor
  (4) Disponibilidad:  x[c,r,t] = 0 si el curso c no puede dictarse en t
                       (se implementa no creando esas variables)

Objetivo: 0 (solo factibilidad). Las restricciones blandas van en la iteracion 2.

Uso (desde la raiz del repo):
    python src/modelo_gurobi.py instancias/itc2007/toytoy.ctt
    python src/modelo_gurobi.py instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4

Escribe la solucion en formato ITC ("curso sala dia periodo" por linea) en
resultados/soluciones/<instancia>_gurobi.sol, para revisarla con src/verificar.py.
"""
import argparse
import time
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from leer_ctt import leer_ctt

RAIZ = Path(__file__).resolve().parent.parent


def construir_modelo(inst, nombre="cbctt"):
    C = list(inst["cursos"])
    R = list(inst["salas"])
    T = inst["slots"]
    P = inst["Periods_per_day"]

    # (4) disponibilidad: solo se crean las variables (c, r, t) permitidas
    def disponible(c, t):
        return (c, t // P, t % P) not in inst["indisponibles"]

    indices = [(c, r, t) for c in C for t in T if disponible(c, t) for r in R]

    m = gp.Model(nombre)
    x = m.addVars(indices, vtype=GRB.BINARY, name="x")

    # (1) cada curso dicta exactamente sus l_c clases
    m.addConstrs((x.sum(c, "*", "*") == inst["cursos"][c]["clases"] for c in C),
                 name="clases")

    # (2) a lo mas una clase por sala y slot
    m.addConstrs((x.sum("*", r, t) <= 1 for r in R for t in T), name="sala")

    # (3a) un curso no dicta dos clases en el mismo slot
    m.addConstrs((x.sum(c, "*", t) <= 1 for c in C for t in T), name="curso_slot")

    # (3b) cursos de un mismo curriculo no se topan
    for q, cursos_q in inst["curriculos"].items():
        for t in T:
            m.addConstr(gp.quicksum(x.sum(c, "*", t) for c in cursos_q) <= 1,
                        name=f"curriculo[{q},{t}]")

    # (3c) cursos de un mismo profesor no se topan
    por_profesor = {}
    for c, datos in inst["cursos"].items():
        por_profesor.setdefault(datos["profesor"], []).append(c)
    for prof, cursos_p in por_profesor.items():
        if len(cursos_p) < 2:
            continue  # con un solo curso ya lo cubre (3a)
        for t in T:
            m.addConstr(gp.quicksum(x.sum(c, "*", t) for c in cursos_p) <= 1,
                        name=f"profesor[{prof},{t}]")

    m.setObjective(0, GRB.MINIMIZE)  # iteracion 1: solo factibilidad
    m.update()
    return m, x


def extraer_solucion(inst, x):
    P = inst["Periods_per_day"]
    return [(c, r, t // P, t % P) for (c, r, t), var in x.items() if var.X > 0.5]


def guardar_solucion(asignaciones, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        for c, r, d, p in sorted(asignaciones):
            f.write(f"{c} {r} {d} {p}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("instancia", help="ruta al archivo .ctt")
    ap.add_argument("--tiempo", type=float, default=60, help="limite de tiempo en segundos")
    ap.add_argument("--hilos", type=int, default=4, help="Threads (usar el mismo en CPLEX)")
    ap.add_argument("--gap", type=float, default=0.0, help="MIPGap (0 = demostrar optimo)")
    args = ap.parse_args()

    inst = leer_ctt(args.instancia)
    nombre = Path(args.instancia).stem
    m, x = construir_modelo(inst, nombre)
    m.Params.TimeLimit = args.tiempo
    m.Params.Threads = args.hilos
    m.Params.MIPGap = args.gap
    (RAIZ / "resultados" / "logs").mkdir(parents=True, exist_ok=True)
    m.Params.LogFile = str(RAIZ / "resultados" / "logs" / f"{nombre}_gurobi.log")

    print(f"{nombre}: {m.NumVars} variables, {m.NumConstrs} restricciones")
    t0 = time.time()
    m.optimize()
    seg = time.time() - t0

    if m.SolCount == 0:
        estado = {GRB.INFEASIBLE: "INFACTIBLE", GRB.TIME_LIMIT: "SIN SOLUCION EN EL LIMITE"}
        print(f"\n{nombre}: {estado.get(m.Status, m.Status)} ({seg:.1f} s)")
        return

    sol = extraer_solucion(inst, x)
    ruta = RAIZ / "resultados" / "soluciones" / f"{nombre}_gurobi.sol"
    guardar_solucion(sol, ruta)
    print(f"\n{nombre}: solucion factible con {len(sol)} clases en {seg:.1f} s -> {ruta.relative_to(RAIZ)}")
    print(f"Revisala con:  python src/verificar.py {args.instancia} {ruta.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
