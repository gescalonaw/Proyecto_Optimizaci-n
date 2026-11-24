#!/bin/bash
# Correr EN Luthier la primera vez:  bash revisar_servidor.sh > info_luthier.txt
# Anota el hardware (va en "supuestos y limitaciones") y que solvers hay.
echo "== Fecha";        date
echo "== Sistema";      uname -a; cat /etc/os-release 2>/dev/null | head -2
echo "== CPU";          lscpu 2>/dev/null | grep -E "Model name|^CPU\(s\)|Thread|Core" || nproc
echo "== RAM";          free -h
echo "== Disco (home)"; df -h ~ | tail -1
echo "== Python";       which python3; python3 --version
echo "== Modulos (si los hay)"; (module avail 2>&1 | grep -iE "gurobi|cplex|python") || echo "sin 'module'"
echo "== Gurobi";       which gurobi_cl && gurobi_cl --version; echo "GUROBI_HOME=$GUROBI_HOME"; ls ~/gurobi.lic /opt/gurobi* 2>/dev/null
python3 -c "import gurobipy as g; print('gurobipy', g.gurobi.version())" 2>&1 | tail -1
echo "== CPLEX";        which cplex; ls -d /opt/ibm* 2>/dev/null
python3 -c "import cplex; print('cplex', cplex.__version__)" 2>&1 | tail -1
python3 -c "import docplex; print('docplex', docplex.__version__)" 2>&1 | tail -1
echo "== tmux/screen";  which tmux screen
