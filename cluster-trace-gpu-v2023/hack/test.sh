#!/bin/bash

source /local/repository/venv/bin/activate

python3 "true-utilization.py" &

python3 podkiller.py &

python3 pods-apply.py &