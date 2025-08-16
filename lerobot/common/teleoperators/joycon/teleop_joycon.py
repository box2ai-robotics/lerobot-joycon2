#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys

import torch
import numpy as np

import time
from queue import Queue
from typing import Any

from lerobot.common.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..teleoperator import Teleoperator
from .configuration_joycon import JoyconTeleopConfig
from .joycon_controller import JoyConController
from lerobot.common.robots import make_robot_from_config

class JoyconTeleop(Teleoperator):
    """
    Teleop class to use joycon inputs for control.
    """

    config_class = JoyconTeleopConfig
    name = "joycon"
    is_joycon = True

    def __init__(self, config: JoyconTeleopConfig):
        super().__init__(config)
        self.config = config
        self.button_control = 0
        self.gripper_state = {}
        self.gripper_state_last = {}
        self.logs = {}
        self.controllers = JoyConController(
            name="right"
        )
    @property
    def action_features(self) -> dict:
        return {
            "dtype": "float32",
            "shape": (len(self.arm),),
            "names": {"motors": list(self.arm.motors)},
        }

    @property
    def feedback_features(self) -> dict:
        return {}

    @property
    def is_connected(self) -> bool:
        return False
    
    @property
    def is_calibrated(self) -> bool:
        pass

    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(
                "Joycon is already connected. Do not run `robot.connect()` twice."
            )
        # self.is_connected = True

    def calibrate(self) -> None:
        pass

    def configure(self):
        pass

    def get_action(self, robot) -> dict[str, Any]:
        leader_pos = {}
        motor_name = list(robot.bus.motors.keys())
        if self.controllers is not None:
            controller_command={}
            name = self.controllers.name
                # Get positions from controller
            before_controller_read_t = time.perf_counter()

            controller_command, button_control, self.gripper_state = self.controllers.get_command()   
            if name == 'right':
                self.button_control = button_control         
            leader_pos = dict(zip([f"{name}.pos" for name in motor_name], controller_command))
            # print(leader_pos)
            self.logs["read_controller_{name}_command_dt_s"] = time.perf_counter() - before_controller_read_t
            return leader_pos

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    def disconnect(self) -> None:
        if not self.is_connected:
            raise DeviceNotConnectedError(
                "JoyconTeleop is not connected. You need to run `robot.connect()` before `disconnect()`."
            )
        if self.listener is not None:
            self.listener.stop()
