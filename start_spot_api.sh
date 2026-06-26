#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Intended use: ./start_spot_api.sh <0/1> where 0 indicates starting without client and 1 indicates starting without"
else
  cd spot_bullet/src
  uv run API_server_d.py &
  echo "============================================================================================="
  if [ $1 -eq 1 ]; then
    echo "============================================================================================="
    uv run API_client_d.py &
  fi
  uv run env_tester_controller.py -dr
fi
