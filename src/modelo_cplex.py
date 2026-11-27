"""Modelo PLE de CB-CTT (ITC-2007 track 3) en CPLEX (docplex): restricciones duras + blandas.

Es el MISMO modelo que src/modelo_gurobi.py (misma notacion y numeracion de restricciones);
ver la formulacion completa alli. Los conjuntos vienen de src/comun.py para que ambos
solvers resuelvan exactamente el mismo problema.

Uso (desde la raiz del repo):
    python src/modelo_cplex.py instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4
    python src/modelo_cplex.py instancias/itc2007/comp01.ctt --solo-duras     (iteracion 1)
"""
import argparse
import time
from pathlib import Path

from docplex.mp.model import Model

from comun import (PESO_CAPACIDAD, PESO_COMPACIDAD, PESO_DIAS, PESO_ESTABILIDAD,
                   guardar_solucion, preparar, ruta_log)
from leer_ctt import leer_ctt


def construir_modelo(inst, nombre="cbctt", solo_duras=False):
    S = preparar(inst)
    C, R, D, T = S["C"], S["R"], S["D"], S["T"]
    m = Model(nombre)

    x = m.binary_var_dict(S["X"], name="x")

    # sumas auxiliares de x (equivalen a x.sum(...) de gurobipy)
    por_curso, por_sala_slot, por_curso_slot = {}, {}, {}
    for (c, r, t), var in x.items():
        por_curso.setdefault(c, []).append(var)
        por_sala_slot.setdefault((r, t), []).append(var)
        por_curso_slot.setdefault((c, t), []).append(var)

    def suma_cs(c, t):
        return m.sum(por_curso_slot.get((c, t), []))

    # ---------------- duras ----------------
    for c in C:
        m.add_constraint(m.sum(por_curso.get(c, [])) == inst["cursos"][c]["clases"], f"clases_{c}")
    for (r, t), vars_rt in por_sala_slot.items():
        m.add_constraint(m.sum(vars_rt) <= 1)
    for (c, t), vars_ct in por_curso_slot.items():
        m.add_constraint(m.sum(vars_ct) <= 1)
    for g, cursos_g in S["grupos"].items():
        for t in T:
            m.add_constraint(m.sum(suma_cs(c, t) for c in cursos_g) <= 1)

    if solo_duras:
        m.minimize(0)
        return m, x

    # ---------------- blandas ----------------
    f_capacidad = m.sum(S["exceso"][c, r] * x[c, r, t] for (c, r, t) in S["X"] if S["exceso"][c, r] > 0)

    y = m.binary_var_dict([(c, d) for c in C for d in D], name="y")
    w = m.continuous_var_dict(C, lb=0, name="w")
    u = m.binary_var_dict(C, name="u")
    for c in C:
        for d in D:
            m.add_constraint(y[c, d] <= m.sum(suma_cs(c, t) for t in S["slots_dia"][d]))
            for t in S["slots_dia"][d]:
                m.add_constraint(y[c, d] >= suma_cs(c, t))
        mnd = inst["cursos"][c]["min_dias"]
        n_c = m.sum(y[c, d] for d in D)
        m.add_constraint(w[c] >= mnd - n_c)
        m.add_constraint(w[c] <= mnd * u[c])
        m.add_constraint(w[c] <= mnd - n_c + mnd * (1 - u[c]))

    curriculos = inst["curriculos"]
    z = {(q, t): m.sum(suma_cs(c, t) for c in cs) for q, cs in curriculos.items() for t in T}
    e = m.continuous_var_dict([(q, t) for q in curriculos for t in T], lb=0, name="e")
    for q in curriculos:
        for t in T:
            m.add_constraint(e[q, t] >= z[q, t] - m.sum(z[q, s] for s in S["vecinos"][t]))
            m.add_constraint(e[q, t] <= z[q, t])
            for s_ in S["vecinos"][t]:
                m.add_constraint(e[q, t] <= 1 - z[q, s_])

    v = m.binary_var_dict([(c, r) for c in C for r in R], name="v")
    por_curso_sala = {}
    for (c, r, t), var in x.items():
        m.add_constraint(var <= v[c, r])
        por_curso_sala.setdefault((c, r), []).append(var)
    for c in C:
        for r in R:
            m.add_constraint(v[c, r] <= m.sum(por_curso_sala.get((c, r), [])))

    m.minimize(PESO_CAPACIDAD * f_capacidad
               + PESO_DIAS * m.sum(w.values())
               + PESO_COMPACIDAD * m.sum(e.values())
               + PESO_ESTABILIDAD * (m.sum(v.values()) - len(C)))
    return m, x


# codigos de estado de CPLEX
ESTADOS = {101: "OPTIMO", 102: "OPTIMO", 107: "LIMITE_TIEMPO", 108: "SIN_SOLUCION",
           103: "INFACTIBLE", 119: "INFACTIBLE"}


def resolver(inst, nombre, tiempo, hilos, gap=0.0, solo_duras=False, mostrar=True):
    """Arma y resuelve el modelo. Devuelve un diccionario con los resultados (lo usa src/correr.py)."""
    t0 = time.time()
    m, x = construir_modelo(inst, nombre, solo_duras)
    t_modelo = time.time() - t0
    m.set_time_limit(tiempo)
    m.parameters.threads = hilos
    m.parameters.mip.tolerances.mipgap = gap
    if mostrar:
        print(f"{nombre}: {m.number_of_variables} variables, {m.number_of_constraints} restricciones")

    t0 = time.time()
    with open(ruta_log(nombre, "cplex"), "w", encoding="utf-8") as log:
        s = m.solve(log_output=log)
    seg = time.time() - t0
    det = m.solve_details

    estado = ESTADOS.get(det.status_code, f"STATUS_{det.status_code}")
    sol = []
    if s is not None:
        P = inst["Periods_per_day"]
        sol = [(c, r, t // P, t % P) for (c, r, t), var in x.items() if s.get_value(var) > 0.5]
    try:
        cota = det.best_bound
    except Exception:
        cota = None
    return {
        "solver": "cplex",
        "version": m.get_cplex().get_version(),
        "estado": estado,
        "tiempo_s": seg,
        "tiempo_modelo_s": t_modelo,
        "objetivo": s.objective_value if s is not None else None,
        "cota": cota,
        "gap": det.mip_relative_gap if s is not None else None,
        "nodos": int(det.nb_nodes_processed or 0),
        "variables": m.number_of_variables,
        "restricciones": m.number_of_constraints,
        "solucion": sol,
    }


def main():
    ap = argparse.ArgumentParser(description="CB-CTT en CPLEX")
    ap.add_argument("instancia", help="ruta al archivo .ctt")
    ap.add_argument("--tiempo", type=float, default=60, help="limite de tiempo en segundos")
    ap.add_argument("--hilos", type=int, default=4, help="threads (usar el mismo en Gurobi)")
    ap.add_argument("--gap", type=float, default=0.0, help="mipgap relativo (0 = demostrar optimo)")
    ap.add_argument("--solo-duras", action="store_true", help="sin restricciones blandas (iteracion 1)")
    args = ap.parse_args()

    inst = leer_ctt(args.instancia)
    nombre = Path(args.instancia).stem
    r = resolver(inst, nombre, args.tiempo, args.hilos, args.gap, args.solo_duras)
    if not r["solucion"]:
        print(f"\n{nombre} [cplex]: {r['estado']} en {r['tiempo_s']:.1f} s")
        return
    ruta = guardar_solucion(r["solucion"], nombre, "cplex")
    print(f"\n{nombre} [cplex]  estado={r['estado']}  objetivo={r['objetivo']:.0f}  cota={r['cota']:.2f}  "
          f"gap={100 * r['gap']:.2f}%  tiempo={r['tiempo_s']:.1f}s")
    print(f"Revisala con:  python src/verificar.py {args.instancia} {ruta.relative_to(ruta.parents[2]).as_posix()}")

if __name__ == "__main__":
    main()
