from typing import (List, Dict)
from mathutils import Quaternion,Vector

class Transform:
    position: Vector
    rotation: Quaternion


class Bone:
    """
    Represents a bone in the bone hierarchy of the model
    """
    name: str
    parent: 'Bone'
    transform: Transform  # transform of this bone relative to its parent. Affine transform without scale


class Vertex:
    """
    Represents one vertex in the model. A vertex has up to 2 UV channels.
    It stores position as well as normal, binormal and tangent vectors.
    """
    position: List[float]
    normal: List[float]
    tangent: List[float]
    binormal: List[float]
    UVs: List[List[float]]  # can contain up to two uv coordinates as XY positions
    bones: List[Bone]  # up to 4 bones which this vertex is parented to


class Face:
    """
    Represents a single face in the mesh
    Note: smooth shaded faces have shared vertices with their neighbouring faces
        and the vertex normals point to the average up vector of the adjacent faces
        Flat shaded faces have split vertices/ normals
    """
    vertices: List[int]  # exactly three vertex indexes of the vertices that make up this face


class Pose:
    """
    Represents a pose of the entire skeleton
    """
    bone_transforms: Dict[Bone, Transform]  # maps each bone to a new transform (no scale)
