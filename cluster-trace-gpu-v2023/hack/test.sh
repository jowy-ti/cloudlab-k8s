#!/bin/bash

source /local/repository/venv/bin/activate

python3 utilization.py &

python3 podkiller.py &

python3 pods-apply.py &