#!/bin/bash
# Correr EN Chome antes de una tanda de corridas oficiales:
#   bash chome/revisar_servidor.sh > resultados/info_servidor_$(date +%F).txt
# Deja registro del hardware y de la carga del servidor (va en "supuestos y limitaciones").
echo "== Fecha";   date
echo "== Sistema"; uname -a; head -2 /etc/os-release 2>/dev/null
echo "== CPU";     lscpu 2>/dev/null | grep -E "Model name|^CPU\(s\)|Thread|Core|Socket" || nproc
echo "== RAM";     free -h
echo "== Carga";   uptime
echo "== Disco";   df -h ~ | tail -1
echo "== Python";  which python; python --version
python -c "import gurobipy as g; print('gurobipy', g.gurobi.version())" 2>&1 | tail -1
python -c "import cplex; print('cplex', cplex.__version__)" 2>&1 | tail -1
ls -l ~/gurobi.lic 2>/dev/null
