"""Verificador independiente del solver para soluciones de CB-CTT (ITC-2007 track 3).

Lee la instancia (.ctt) y una solucion en formato ITC ("curso sala dia periodo" por linea)
y cuenta:
  - violaciones DURAS: clases (faltan/sobran/repetidas en un slot), ocupacion de sala,
    conflictos (curriculo y profesor) y disponibilidad;
  - costo de las restricciones BLANDAS con los pesos del ITC-2007:
    capacidad (1 por alumno de mas), dias minimos (5 por dia faltante),
    compacidad del curriculo (2 por clase aislada), estabilidad de sala (1 por sala extra).

En la iteracion 2, el costo blando que calcula este script debe ser IGUAL al objetivo del solver.

Uso:
    python src/verificar.py instancias/itc2007/comp01.ctt resultados/soluciones/comp01_gurobi.sol
"""
import sys
from collections import Counter, defaultdict

from leer_ctt import leer_ctt


def leer_solucion(ruta):
    sol = []
    with open(ruta, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            if linea.strip():
                c, r, d, p = linea.split()
                sol.append((c, r, int(d), int(p)))
    return sol


def verificar(inst, sol):
    cursos, salas = inst["cursos"], inst["salas"]
    duras = Counter()
    detalle = []

    # --- datos inconsistentes (curso/sala/slot que no existen)
    validas = []
    for c, r, d, p in sol:
        if c not in cursos or r not in salas or not (0 <= d < inst["Days"]) or not (0 <= p < inst["Periods_per_day"]):
            duras["linea_invalida"] += 1
            detalle.append(f"linea invalida: {c} {r} {d} {p}")
        else:
            validas.append((c, r, d, p))

    # --- (1) clases: cada curso con exactamente l_c clases, en slots distintos
    por_curso = defaultdict(list)
    for c, r, d, p in validas:
        por_curso[c].append((d, p))
    for c, datos in cursos.items():
        n = len(por_curso[c])
        if n != datos["clases"]:
            duras["clases"] += abs(datos["clases"] - n)
            detalle.append(f"clases: {c} tiene {n} de {datos['clases']}")
        for (d, p), k in Counter(por_curso[c]).items():
            if k > 1:
                duras["clases"] += k - 1
                detalle.append(f"clases: {c} tiene {k} clases en el dia {d} periodo {p}")

    # --- (2) ocupacion: una clase por sala y slot
    for (r, d, p), k in Counter((r, d, p) for _, r, d, p in validas).items():
        if k > 1:
            duras["sala"] += k - 1
            detalle.append(f"sala: {r} tiene {k} clases en el dia {d} periodo {p}")

    # --- (3) conflictos de curriculo y de profesor
    for q, cursos_q in inst["curriculos"].items():
        miembros = set(cursos_q)
        for (d, p), k in Counter((d, p) for c, _, d, p in validas if c in miembros).items():
            if k > 1:
                duras["curriculo"] += k - 1
                detalle.append(f"curriculo: {q} tiene {k} clases en el dia {d} periodo {p}")
    for (prof, d, p), k in Counter((cursos[c]["profesor"], d, p) for c, _, d, p in validas).items():
        if k > 1:
            duras["profesor"] += k - 1
            detalle.append(f"profesor: {prof} tiene {k} clases en el dia {d} periodo {p}")

    # --- (4) disponibilidad
    for c, r, d, p in validas:
        if (c, d, p) in inst["indisponibles"]:
            duras["disponibilidad"] += 1
            detalle.append(f"disponibilidad: {c} no puede el dia {d} periodo {p}")

    # --- blandas (pesos ITC-2007)
    blandas = Counter()
    for c, r, d, p in validas:  # capacidad
        blandas["capacidad"] += max(0, cursos[c]["alumnos"] - salas[r])
    for c, datos in cursos.items():  # dias minimos
        dias = len({d for d, _ in por_curso[c]})
        blandas["dias_minimos"] += 5 * max(0, datos["min_dias"] - dias)
    for q, cursos_q in inst["curriculos"].items():  # compacidad
        miembros = set(cursos_q)
        ocupados = Counter((d, p) for c, _, d, p in validas if c in miembros)
        for (d, p), k in ocupados.items():
            if (d, p - 1) not in ocupados and (d, p + 1) not in ocupados:
                blandas["compacidad"] += 2 * k
    salas_curso = defaultdict(set)
    for c, r, _, _ in validas:  # estabilidad de sala
        salas_curso[c].add(r)
    for c in cursos:
        blandas["estabilidad_sala"] += max(0, len(salas_curso[c]) - 1)

    return duras, blandas, detalle


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    inst = leer_ctt(sys.argv[1])
    sol = leer_solucion(sys.argv[2])
    duras, blandas, detalle = verificar(inst, sol)

    print(f"Instancia {inst['Name']} | {len(sol)} clases en la solucion")
    print("\nVIOLACIONES DURAS")
    for k in ("clases", "sala", "curriculo", "profesor", "disponibilidad", "linea_invalida"):
        print(f"  {k:<16} {duras[k]}")
    total_duras = sum(duras.values())
    print(f"  {'TOTAL':<16} {total_duras}  ->  {'FACTIBLE' if total_duras == 0 else 'INFACTIBLE'}")
    for linea in detalle[:20]:
        print("   -", linea)
    if len(detalle) > 20:
        print(f"   ... y {len(detalle) - 20} mas")

    print("\nCOSTO BLANDO (pesos ITC-2007)")
    for k in ("capacidad", "dias_minimos", "compacidad", "estabilidad_sala"):
        print(f"  {k:<16} {blandas[k]}")
    print(f"  {'TOTAL':<16} {sum(blandas.values())}")
    sys.exit(0 if total_duras == 0 else 2)


if __name__ == "__main__":
    main()
