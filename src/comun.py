"""Datos derivados de una instancia CB-CTT, compartidos por modelo_gurobi.py y modelo_cplex.py.

Asi los dos solvers arman EXACTAMENTE el mismo modelo (mismos conjuntos e indices).
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# se anota en cada fila de resultados/tabla.csv; cambiarla si cambia la formulacion
VERSION_MODELO = "v2-exacto"

# pesos de las restricciones blandas (ITC-2007, track 3)
PESO_CAPACIDAD = 1      # por alumno que no cabe en la sala
PESO_DIAS = 5           # por dia faltante bajo el minimo de dias de trabajo
PESO_COMPACIDAD = 2     # por clase aislada de un curriculo
PESO_ESTABILIDAD = 1    # por sala distinta extra que usa un curso


def preparar(inst):
    """Conjuntos e indices del modelo.

    C cursos, R salas, D dias, T slots (t = d * P + p).
    X       indices (c, r, t) permitidos (la indisponibilidad se aplica aqui).
    grupos  conjuntos de cursos que no pueden dictarse en el mismo slot:
            cada curriculo y cada profesor con 2 o mas cursos.
    vecinos para cada slot t, los slots adyacentes DEL MISMO DIA (para compacidad).
    """
    P = inst["Periods_per_day"]
    C = list(inst["cursos"])
    R = list(inst["salas"])
    D = inst["dias"]
    T = inst["slots"]

    X = [(c, r, t) for c in C for t in T
         if (c, t // P, t % P) not in inst["indisponibles"] for r in R]

    por_profesor = {}
    for c, datos in inst["cursos"].items():
        por_profesor.setdefault(datos["profesor"], []).append(c)
    grupos = {f"curriculo:{q}": cs for q, cs in inst["curriculos"].items()}
    grupos.update({f"profesor:{p}": cs for p, cs in por_profesor.items() if len(cs) > 1})

    vecinos = {t: [s for s in (t - 1, t + 1) if 0 <= s < len(T) and s // P == t // P] for t in T}
    slots_dia = {d: [t for t in T if t // P == d] for d in D}

    exceso = {(c, r): max(0, inst["cursos"][c]["alumnos"] - inst["salas"][r]) for c in C for r in R}

    return {"C": C, "R": R, "D": D, "T": T, "P": P, "X": X, "grupos": grupos,
            "vecinos": vecinos, "slots_dia": slots_dia, "exceso": exceso}


def guardar_solucion(asignaciones, nombre, solver):
    """Escribe la solucion en formato ITC: 'curso sala dia periodo' por linea."""
    ruta = RAIZ / "resultados" / "soluciones" / f"{nombre}_{solver}.sol"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        for c, r, d, p in sorted(asignaciones):
            f.write(f"{c} {r} {d} {p}\n")
    return ruta


def ruta_log(nombre, solver):
    ruta = RAIZ / "resultados" / "logs" / f"{nombre}_{solver}.log"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta
