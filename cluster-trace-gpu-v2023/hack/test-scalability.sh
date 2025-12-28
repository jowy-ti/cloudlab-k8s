#!/bin/bash

source /local/repository/venv/bin/activate

python3 scale-evaluation.py &

python3 podkiller.py &

sleep 5

python3 pods-apply.py &