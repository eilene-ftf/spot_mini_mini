#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Intended use: ./start_spot_api.sh <0/1/2> where 0 indicates starting without client and 1 indicates starting with; 2 indicates client only, not running the sim"
elif [ $1 -eq 2 ]; then
  echo "Starting client"
  cd spot_bullet/src
  uv run API_client_d.py
else
  echo "Starting server"
  cd spot_bullet/src
  uv run API_server_d.py &
  if [ $1 -eq 1 ]; then
    echo "Starting client"
    uv run API_client_d.py &
  fi
  echo "Starting sim"
  echo "============================================================================================="
  uv run env_tester_controller.py -dr
fi
