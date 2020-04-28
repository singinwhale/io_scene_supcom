from typing import List

from PySupComIO.common_types import Pose, Bone


class Frame:
    time: float
    flags: int
    pose: Pose


class Animation:
    duration: float
    bones: List[Bone]
    initial_pose: Pose
    frames: List[Frame]
