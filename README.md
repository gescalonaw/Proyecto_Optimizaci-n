# Asignación óptima de horarios y salas mediante PLE

Proyecto de Optimización (UdeC, 2026-2). Se modela el problema de horarios por plan de estudios (CB-CTT, ITC-2007 track 3) como un PLE, se resuelve con **Gurobi** y **CPLEX** y se comparan tiempo, MIPGap y mejor solución con un límite de 1 h por instancia en el servidor **Chome**.

## Entrar al servidor y ver las corridas

Las corridas oficiales se ejecutan en **Chome** (`chome.inf.udec.cl`), con la cuenta del grupo `grupo03`. Gurobi y CPLEX ya están instalados ahí con licencia académica, así que **no hay que instalar nada en el PC** para ver resultados. Las credenciales están en el grupo y **no van en este repo**.

### 1. Conectarse

Desde Git Bash (Windows) o una terminal (Linux/Mac), desde cualquier red, sin VPN:

    ssh grupo03@chome.inf.udec.cl

La contraseña no se ve mientras se escribe. La primera vez pregunta si confías en el servidor: responder `yes`. Para salir: `exit`.

### 2. Entrar al proyecto (siempre, cada vez que se entra)

    cd ~/Proyecto_Optimizaci-n
    source .venv/bin/activate

El prompt tiene que quedar como `(.venv) grupo03@chome:~/Proyecto_Optimizaci-n$`. Sin `(.venv)` se usa el Python 2.7 del servidor y nada funciona.

### 3. Ver si hay corridas en curso

Las corridas largas viven en sesiones de **tmux**, que siguen corriendo aunque nadie esté conectado.

    tmux ls                  # lista las sesiones (por ejemplo A, B y C)
    tmux attach -t A -r      # mirar la sesión A en modo SOLO LECTURA

Dentro se ve el avance, por ejemplo `[3/6] comp18 con gurobi, modelo v1 (3600 s, 8 hilos)`. Cada corrida imprime su resultado al terminar. Para salir **sin detener nada**: `Ctrl+b` y luego `d`.

Siempre usar `-r` para mirar: sin eso, un `Ctrl+C` por error mata la corrida. Si `tmux ls` dice `no server running`, no hay corridas activas.

### 4. Ver los resultados

    python src/comparar.py --tiempo 3600     # tabla Gurobi vs CPLEX de las corridas de 1 h
    python src/graficos.py                   # genera las figuras en resultados/figuras/

`comparar.py` muestra solo las corridas que ya terminaron, así que se puede correr en cualquier momento. Para la prueba de 10 min: `--tiempo 600`. El "costo" es el costo real del horario medido por `verificar.py`, y el gap usa la cota del solver recortada en 0 (`*` = la cota era negativa).

### 5. Traer los resultados al PC

Desde Git Bash **en el PC**, dentro de la carpeta del repo:

    scp -r grupo03@chome.inf.udec.cl:~/Proyecto_Optimizaci-n/resultados/figuras ./resultados/
    scp grupo03@chome.inf.udec.cl:~/Proyecto_Optimizaci-n/resultados/comparacion.csv ./resultados/

### Reglas en Chome

- En Chome **solo se hace `git pull` y se corre**. Nunca `git add` ni `git commit` ahí: se programa en el PC y se sube con push.
- No hacer `git pull` mientras hay corridas activas.
- No lanzar corridas propias mientras estén las oficiales: cambian la carga del servidor y afectan los tiempos.
- Las corridas largas van siempre dentro de tmux (`tmux new -s nombre`, luego `Ctrl+b` y `d` para salir).
- Si hay que pegar varios comandos, primero `tmux new -s nombre` solo, y el resto después de que aparezca la barra verde.

Más detalles del servidor (hardware, cómo quedó instalado, arreglo de CPLEX): [chome/GUIA_CHOME.md](chome/GUIA_CHOME.md).

## Estructura

    instancias/itc2007/       comp01–comp21 + toy/toytoy (fuente: github.com/Docheinstein/itc2007-cct)
    instancias/oficiales.txt  las 9 instancias de las corridas oficiales y por qué (3 por característica)
    instancias/resumen.csv    características de cada instancia (python src/resumen_instancias.py)
    src/leer_ctt.py           lector de archivos .ctt
    src/comun.py              conjuntos, índices, pesos y versiones del modelo (v1 / v2)
    src/modelo_gurobi.py      modelo PLE (duras + blandas) en Gurobi; formulación comentada al inicio
    src/modelo_cplex.py       el mismo modelo en CPLEX (docplex)
    src/verificar.py          revisa una solución sin usar el solver: violaciones duras y costo real
    src/prueba_licencias.py   prueba que ambos solvers tengan licencia completa
    src/correr.py             corre ambos solvers sobre varias instancias y anota en resultados/tabla.csv
    src/comparar.py           tabla Gurobi vs CPLEX por instancia (resultados/comparacion.csv)
    src/graficos.py           figuras de costo, gap y tiempo (resultados/figuras/)
    resultados/               tabla, soluciones, logs y figuras; los .csv no se suben al repo
    chome/                    guía del servidor y script para ver su hardware
    informe/                  plan del proyecto

## Versiones del modelo

- **v1 (base):** las variables auxiliares de las penalizaciones solo tienen cota inferior. Es la que se usa en las corridas oficiales: fue más rápida en la prueba de 10 min, sobre todo con CPLEX.
- **v2 (exacta):** agrega cotas superiores para que el objetivo de cualquier solución sea su costo real.

Ambas tienen el mismo óptimo. Con v1, una solución no óptima puede reportar un objetivo mayor que su costo real (`verif_ok = SOBREESTIMA`); por eso los resultados se comparan siempre con el costo que mide `verificar.py`.

## Uso en un PC

    python src/modelo_gurobi.py instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4 --version v1
    python src/modelo_cplex.py  instancias/itc2007/comp01.ctt --tiempo 60 --hilos 4 --version v1
    python src/verificar.py instancias/itc2007/comp01.ctt resultados/soluciones/comp01_gurobi.sol

- `--tiempo` límite en segundos, `--hilos` threads (el MISMO en ambos solvers), `--gap` MIPGap relativo (0 por defecto), `--version` v1 o v2 (v2 por defecto), `--solo-duras` sin restricciones blandas.

Corridas por lote (en Chome, dentro de tmux):

    python src/correr.py comp01 comp11 --versiones v1 --tiempo 60 --hilos 8                  # prueba corta
    python src/correr.py --lista instancias/oficiales.txt --versiones v1 --tiempo 3600 --hilos 8

`correr.py` agrega una fila por corrida a `resultados/tabla.csv` apenas termina (estado, tiempo, objetivo, cota, gap, nodos, verificación, carga del servidor). Si se corta, se relanza el mismo comando y salta lo ya corrido.

## Puesta en marcha en un PC (solo para programar)

    git clone https://github.com/gescalonaw/Proyecto_Optimizaci-n.git
    cd Proyecto_Optimizaci-n
    python -m venv .venv
    .venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
    pip install -r requirements.txt
    python src/prueba_licencias.py   # debe decir [OK] en Gurobi y CPLEX con el mismo obj

- **Gurobi:** licencia Academic Named-User desde gurobi.com con el correo @udec.cl. Se crea **solo desde la red UdeC** (o eduroam); después funciona desde cualquier red. La versión de `gurobipy` debe ser la misma que la de la licencia (licencia 13 → `gurobipy==13.*`). Cada licencia queda amarrada a un computador.
- **CPLEX:** instalar CPLEX Optimization Studio académico (IBM SkillsBuild) y después `docplex config --upgrade "<carpeta de CPLEX>"`. Sin ese paso queda el `cplex` de pip en versión Community (máx. 1.000 variables).

Para ver resultados no hace falta nada de esto: basta con entrar a Chome.

## Estado

- [x] Iteración 0: repo, instancias, licencias académicas en PC y en Chome
- [x] Iteración 1: modelo con restricciones duras + verificador
- [x] Iteración 2: restricciones blandas + modelo CPLEX
- [x] Iteración 3: `correr.py`, `comparar.py` y piloto en Chome
- [ ] Iteración 4: 9 instancias oficiales elegidas; corridas de 1 h en curso (27-11)
- [ ] Iteración 5: análisis, supuestos y limitaciones, presentación