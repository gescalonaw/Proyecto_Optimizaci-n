# Asignación óptima de horarios y salas mediante PLE

Proyecto de Optimización (UdeC, 2026-2). Se modela el problema de horarios por plan de estudios (CB-CTT, ITC-2007 track 3) como un PLE, se resuelve con **Gurobi** y **CPLEX** y se comparan tiempo, MIPGap y mejor solución con un límite de 1 h por instancia.

## Estructura

    instancias/itc2007/   comp01–comp21 + toy/toytoy (fuente: github.com/Docheinstein/itc2007-cct)
    instancias/propias/   sub-instancias o instancias creadas por el grupo
    instancias/resumen.csv  características de cada instancia (python src/resumen_instancias.py)
    src/                  código (lector, modelo Gurobi, modelo CPLEX, verificador, corridas)
    resultados/           tabla.csv con las corridas, logs/ con los .log de los solvers
    luthier/              guía y script para el servidor
    informe/              material para la presentación final

## Puesta en marcha (cada integrante)

    python -m venv .venv
    .venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
    pip install -r requirements.txt
    python src/leer_ctt.py instancias/itc2007/comp01.ctt
    python src/prueba_licencias.py   # debe decir [OK] en Gurobi y CPLEX

- **Gurobi:** licencia Academic Named-User (en la red UdeC) o Academic WLS (fuera de la red) desde gurobi.com con el correo @udec.cl. Sin ella, el pip trae una licencia limitada a 2.000 variables, y comp01 ya tiene 5.400 solo en x.
- **CPLEX:** CPLEX académico (IBM SkillsBuild / Academic Initiative) y luego `docplex config --upgrade <ruta_cplex>`. El `cplex` de pip es Community Edition (máx. 1.000 variables).

## Estado del plan

- [ ] Iteración 0: repo, licencias OK en ambos solvers, acceso a Luthier probado, fecha confirmada
- [ ] Iteración 1: modelo con restricciones duras + verificador
- [ ] Iteración 2: restricciones blandas + CPLEX
- [ ] Iteración 3: `correr.py` y piloto de 60 s
- [ ] Iteración 4: selección de instancias + corridas de 1 h en Luthier
- [ ] Iteración 5: análisis, supuestos y presentación
