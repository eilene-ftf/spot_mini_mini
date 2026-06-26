#!/usr/bin/env python
"""
env_tester_file.py  –  Spot Mini Mini driven by robot_cmd.json
Drop this into spot_bullet/src/ alongside env_tester.py and run:
    uv run env_tester_file.py -dr
In another terminal run cmd_writer.py to send GO / STOP commands.
"""

import numpy as np
import copy, sys, os, json, argparse

sys.path.append('../../')

from spotmicro.GymEnvs.spot_bezier_env import spotBezierEnv
from spotmicro.Kinematics.SpotKinematics import SpotModel
from spotmicro.Kinematics.LieAlgebra import RPY
from spotmicro.GaitGenerator.Bezier import BezierGait
from spotmicro.spot_env_randomizer import SpotEnvRandomizer
from spotmicro.OpenLoopSM.SpotOL import BezierStepper

# ── Command file (same folder as this script) ──────────────────────────────
CMD_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "robot_cmd.json")

# Safe defaults (STOP state)
DEFAULT_CMD = {
    "go": 0,
    "step_length":       0.0,
    "lateral_fraction":  0.0,
    "yaw_rate":          0.0,
    "step_velocity":     0.001,
    "clearance_height":  0.045,
    "penetration_depth": 0.003,
    "swing_period":      0.2,
}


def read_cmd():
    """Read latest command from file. Falls back to STOP on any error."""
    try:
        with open(CMD_FILE) as f:
            cmd = json.load(f)
        return cmd
    except Exception:
        return DEFAULT_CMD


# ── Args ───────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Spot env driven by robot_cmd.json")
parser.add_argument("-hf", "--HeightField", action='store_true')
parser.add_argument("-r",  "--DebugRack",   action='store_true')
parser.add_argument("-p",  "--DebugPath",   action='store_true')
parser.add_argument("-ar", "--AutoReset",   action='store_true')
parser.add_argument("-dr", "--DontRandomize", action='store_true')
ARGS = parser.parse_args()


def main():
    print("STARTING SPOT (file-driven mode)")
    print(f"Reading commands from: {CMD_FILE}")

    # Write a default STOP command if file doesn't exist yet
    if not os.path.exists(CMD_FILE):
        with open(CMD_FILE, "w") as f:
            json.dump(DEFAULT_CMD, f, indent=2)
        print("Created default robot_cmd.json (STOP state)")

    seed = 0
    max_timesteps = 4e6

    my_path     = os.path.abspath(os.path.dirname(__file__))
    results_path = os.path.join(my_path, "../results")
    models_path  = os.path.join(my_path, "../models")
    os.makedirs(results_path, exist_ok=True)
    os.makedirs(models_path,  exist_ok=True)

    env_randomizer = None if ARGS.DontRandomize else SpotEnvRandomizer()

    env = spotBezierEnv(
        render=True,
        on_rack=ARGS.DebugRack,
        height_field=ARGS.HeightField,
        draw_foot_path=ARGS.DebugPath,
        env_randomizer=env_randomizer,
    )

    env.seed(seed)
    np.random.seed(seed)

    print(f"STATE DIM:  {env.observation_space.shape[0]}")
    print(f"ACTION DIM: {env.action_space.shape[0]}")

    state  = env.reset()
    spot   = SpotModel()
    T_bf0  = spot.WorldToFoot
    T_bf   = copy.deepcopy(T_bf0)
    bzg    = BezierGait(dt=env._time_step)
    bz_step = BezierStepper(dt=env._time_step, mode=0)
    action = env.action_space.sample()

    print("RUNNING  –  edit robot_cmd.json or use cmd_writer.py to control Spot")

    t = 0
    while t < int(max_timesteps):

        bz_step.ramp_up()

        # Get base pos/orn from the state machine
        pos, orn, StepLength, LateralFraction, YawRate, StepVelocity, \
            ClearanceHeight, PenetrationDepth = bz_step.StateMachine()

        # ── Read command from file (replaces GUI sliders) ──────────────────
        cmd = read_cmd()

        if cmd.get("go", 0) == 0:
            # STOP: zero out motion params
            StepLength      = 0.0
            LateralFraction = 0.0
            YawRate         = 0.0
            StepVelocity    = 0.001
        else:
            # GO: use values from file
            StepLength      = cmd.get("step_length",      0.05)
            LateralFraction = cmd.get("lateral_fraction", 0.0)
            YawRate         = cmd.get("yaw_rate",         0.0)
            StepVelocity    = cmd.get("step_velocity",    0.5)

        ClearanceHeight  = cmd.get("clearance_height",  0.045)
        PenetrationDepth = cmd.get("penetration_depth", 0.003)
        SwingPeriod      = cmd.get("swing_period",      0.2)
        # ───────────────────────────────────────────────────────────────────

        bzg.Tswing = SwingPeriod
        yaw = env.return_yaw()

        bz_step.StepLength      = StepLength
        bz_step.LateralFraction = LateralFraction
        bz_step.YawRate         = YawRate
        bz_step.StepVelocity    = StepVelocity

        contacts = state[-4:]

        T_bf = bzg.GenerateTrajectory(
            StepLength, LateralFraction, YawRate, StepVelocity,
            T_bf0, T_bf, ClearanceHeight, PenetrationDepth, contacts
        )

        joint_angles = spot.IK(orn, pos, T_bf)

        env.pass_joint_angles(joint_angles.reshape(-1))
        env.spot.GetExternalObservations(bzg, bz_step)
        state, reward, done, _ = env.step(action)

        if done:
            print("DONE")
            if ARGS.AutoReset:
                env.reset()

        t += 1

    env.close()


if __name__ == '__main__':
    main()


