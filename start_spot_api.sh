#!/bin/bash

cd spot_bullet/src
uv run API_server_d.py &
uv run API_client_d.py &
uv run env_tester_controller.py -dr
