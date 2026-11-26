# Asignación óptima de horarios y salas mediante PLE

Proyecto de Optimización (UdeC, 2026-2). Se modela el problema de horarios por plan de estudios (CB-CTT, ITC-2007 track 3) como un PLE, se resuelve con **Gurobi** y **CPLEX** y se comparan tiempo, MIPGap y mejor solución con un límite de 1 h por instancia en el servidor **Chome**.

## Estructura

    instancias/itc2007/     comp01–comp21 + toy/toytoy (fuente: github.com/Docheinstein/itc2007-cct)
    instancias/propias/     sub-instancias o instancias creadas por el grupo
    instancias/resumen.csv  características de cada instancia (python src/resumen_instancias.py)
    src/leer_ctt.py         lector de archivos .ctt
    src/comun.py            conjuntos, índices y pesos compartidos por los dos modelos
    src/modelo_gurobi.py    modelo PLE (duras + blandas) en Gurobi; formulación comentada al inicio
    src/modelo_cplex.py     el mismo modelo en CPLEX (docplex)
    src/verificar.py        revisa una solución sin usar el solver: violaciones duras y costo blando
    src/prueba_licencias.py prueba que ambos solvers tengan licencia completa
    src/correr.py           corre ambos solvers sobre varias instancias y anota en resultados/tabla.csv
    src/comparar.py         muestra la tabla como Gurobi vs CPLEX por instancia
    resultados/             soluciones (.sol) y logs; no se suben al repo
    chome/                  guía del servidor y script para ver su hardware
    informe/                plan del proyecto y material para la presentación

## Uso

    python src/modelo_gurobi.py instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4
    python src/modelo_cplex.py  instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4
    python src/verificar.py instancias/itc2007/comp01.ctt resultados/soluciones/comp01_gurobi.sol

- `--tiempo` límite en segundos, `--hilos` threads (usar el MISMO en ambos solvers), `--gap` MIPGap relativo (0 por defecto), `--solo-duras` sin restricciones blandas.
- El objetivo que imprime cada solver debe ser igual al TOTAL del costo blando del verificador.

Corridas por lote (en Chome, dentro de tmux):

    python src/correr.py comp01 comp11 --tiempo 60 --hilos 8           # piloto
    python src/correr.py --lista instancias/oficiales.txt --tiempo 3600 --hilos 8
    python src/comparar.py --tiempo 3600 --hilos 8

`correr.py` agrega una fila por corrida a `resultados/tabla.csv` apenas termina (estado, tiempo, objetivo, cota, gap, nodos, verificación, carga del servidor). Si se corta, se relanza el mismo comando y salta lo ya corrido.

## Puesta en marcha en un PC (cada integrante)

    python -m venv .venv
    .venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
    pip install -r requirements.txt
    python src/prueba_licencias.py   # debe decir [OK] en Gurobi y CPLEX con el mismo obj

- **Gurobi:** licencia Academic Named-User desde gurobi.com con el correo @udec.cl. Se crea **solo desde la red UdeC** (o eduroam); después funciona desde cualquier red. La versión de `gurobipy` debe ser la misma que la de la licencia (licencia 13 → `gurobipy==13.*`). Cada licencia queda amarrada a un computador.
- **CPLEX:** instalar CPLEX Optimization Studio académico (IBM SkillsBuild) y después `docplex config --upgrade "<carpeta de CPLEX>"`. Sin ese paso queda el `cplex` de pip en versión Community (máx. 1.000 variables).

Para el servidor, ver [chome/GUIA_CHOME.md](chome/GUIA_CHOME.md).

## Estado

- [x] Iteración 0: repo, instancias, licencias académicas en PC y en Chome
- [x] Iteración 1: modelo con restricciones duras + verificador
- [x] Iteración 2: restricciones blandas + modelo CPLEX
- [x] Iteración 3: `correr.py` y `comparar.py` (piloto pendiente en Chome)
- [ ] Iteración 4: selección de instancias + corridas de 1 h en Chome
- [ ] Iteración 5: análisis, supuestos y presentación
