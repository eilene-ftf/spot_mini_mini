#!/usr/bin/env python
"""
cmd_writer.py  –  Send GO / STOP commands to Spot via robot_cmd.json
Run this in a second terminal while env_tester_file.py is running.

Commands:
  go                          → walk with defaults
  go <step> <lat> <yaw> <vel> → walk with custom params
  stop                        → stand still
  quit / q                    → exit

Example:
  go                  # walk forward at default speed
  go 0.1 0.0 0.0 0.5 # longer steps, same defaults
  go 0.05 0.3 0.0 0.5 # strafe left
  stop
"""

import json, os, sys

CMD_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "robot_cmd.json")

GO_DEFAULTS = {
    "go": 1,
    "step_length":       0.05,
    "lateral_fraction":  0.0,
    "yaw_rate":          0.0,
    "step_velocity":     0.5,
    "clearance_height":  0.045,
    "penetration_depth": 0.003,
    "swing_period":      0.2,
}

STOP_CMD = {
    "go": 0,
    "step_length":       0.0,
    "lateral_fraction":  0.0,
    "yaw_rate":          0.0,
    "step_velocity":     0.001,
    "clearance_height":  0.045,
    "penetration_depth": 0.003,
    "swing_period":      0.2,
}


def write_cmd(cmd):
    with open(CMD_FILE, "w") as f:
        json.dump(cmd, f, indent=2)
    label = "GO  ✓" if cmd["go"] else "STOP ✓"
    print(f"  [{label}]  step={cmd['step_length']:.3f}  "
          f"lat={cmd['lateral_fraction']:.3f}  "
          f"yaw={cmd['yaw_rate']:.3f}  "
          f"vel={cmd['step_velocity']:.3f}")


def main():
    print("Spot cmd_writer  –  type 'go', 'stop', or 'quit'")
    print(f"Writing to: {CMD_FILE}\n")

    # Start in STOP state
    write_cmd(STOP_CMD)

    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nStopping Spot and exiting.")
            write_cmd(STOP_CMD)
            sys.exit(0)

        if not raw:
            continue

        parts = raw.split()
        verb  = parts[0]

        if verb in ("quit", "q", "exit"):
            write_cmd(STOP_CMD)
            print("Sent STOP, bye.")
            break

        elif verb == "stop":
            write_cmd(STOP_CMD)

        elif verb == "go":
            cmd = dict(GO_DEFAULTS)  # copy defaults
            try:
                if len(parts) >= 2: cmd["step_length"]      = float(parts[1])
                if len(parts) >= 3: cmd["lateral_fraction"] = float(parts[2])
                if len(parts) >= 4: cmd["yaw_rate"]         = float(parts[3])
                if len(parts) >= 5: cmd["step_velocity"]    = float(parts[4])
            except ValueError:
                print("  Bad args. Usage: go [step_length lat yaw vel]")
                continue
            write_cmd(cmd)

        else:
            print("  Unknown command. Try: go / stop / quit")


if __name__ == "__main__":
    main()


