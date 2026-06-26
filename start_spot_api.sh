#!/bin/bash

cd spot_bullet/src
uv run API_server_d.py &
echo "============================================================================================="
if [ $1 -eq 1 ]; then
  echo "============================================================================================="
  uv run API_client_d.py &
fi
uv run env_tester_controller.py -dr
