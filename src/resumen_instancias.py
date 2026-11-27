"""Calcula las caracteristicas de cada instancia y las guarda en instancias/resumen.csv.
Sirve para elegir y justificar las instancias oficiales (iteracion 4).

Caracteristicas:
  tamano        cursos, clases y variables x del modelo (indices (c, r, t) permitidos)
  ocupacion_%   clases / (salas * slots): que tan llenas quedan las salas
  conflictos    vecinos_conflicto = promedio de cursos con los que cada curso no puede coincidir
                (mismo curriculo o profesor); indisponible_% = pares (curso, slot) prohibidos

Uso (desde la raiz del repo):  python src/resumen_instancias.py
"""
import csv
from pathlib import Path

from comun import preparar
from leer_ctt import leer_ctt

RAIZ = Path(__file__).resolve().parent.parent
filas = []
for ruta in sorted((RAIZ / "instancias").rglob("*.ctt")):
    i = leer_ctt(ruta)
    S = preparar(i)
    C = len(i["cursos"])
    clases = sum(c["clases"] for c in i["cursos"].values())
    slots, salas = len(i["slots"]), len(i["salas"])
    pares = {(a, b) for cs in S["grupos"].values() for a in cs for b in cs if a < b}
    filas.append({
        "archivo": ruta.relative_to(RAIZ / "instancias").as_posix(),
        "nombre": i["Name"],
        "cursos": C,
        "clases": clases,
        "salas": salas,
        "dias": i["Days"],
        "periodos_dia": i["Periods_per_day"],
        "slots": slots,
        "curriculos": len(i["curriculos"]),
        "variables_x": len(S["X"]),
        "ocupacion_%": round(100 * clases / (salas * slots), 1),
        "vecinos_conflicto": round(2 * len(pares) / C, 1),
        "indisponible_%": round(100 * i["Constraints"] / (C * slots), 1),
    })

with open(RAIZ / "instancias" / "resumen.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)

print(f"{'archivo':<22}{'cursos':>7}{'clases':>7}{'salas':>6}{'slots':>6}{'x':>7}{'ocup%':>7}{'confl':>6}{'indisp%':>8}")
for f in filas:
    print(f"{f['archivo']:<22}{f['cursos']:>7}{f['clases']:>7}{f['salas']:>6}{f['slots']:>6}{f['variables_x']:>7}"
          f"{f['ocupacion_%']:>7}{f['vecinos_conflicto']:>6}{f['indisponible_%']:>8}")
