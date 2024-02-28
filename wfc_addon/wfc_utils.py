from __future__ import annotations
from copy import deepcopy
from typing import List, Tuple
from math import atan2, pi
from enum import Enum
import bpy

LOG_PATH = bpy.path.abspath('//log.txt')
DUMP_DATA_PATH = bpy.path.abspath('//dump.txt')
JSON_DATA_PATH = bpy.path.abspath('//data.json')

# Tuple indices for neighbour association
PX = 0 # LEFT
PY = 1 # BACKWARDS
NX = 2 # RIGHT
NY = 3 # FORWARD
NZ = 4 # DOWN
PZ = 5 # UP

def rotate_list(l: List, n: int):
    return l[n:] + l[:n]

class FaceProfile:
    def __init__(self, uid: int, vertical: bool = False, rotating: bool = False, rotation: int = 0) -> None:
        self.id = uid
        self.vertical = vertical
        self.rotating = rotating
        self.flipping = rotating
        self.rotation = rotation
        self.flipped = bool(rotation)
        self.potential_neighbours: List[int] = []

    def __str__(self) -> str:
        name = str(self.id)
        if self.id == -1:
            return name
        if self.vertical:
            name = 'v' + name + '_' + str(self.rotation) if self.rotating else 'i'
        else:
            if self.flipping:
                name += 'f' if self.flipped else ''
            else:
                name += 's'
        return name

    def get_rotated(self, n: int) -> FaceProfile:
        self.rotation = n
        return deepcopy(self)

class Prototype:
    prototype_count = 0

    def __init__(self, name: str, weight: int, face_profiles: Tuple[FaceProfile], rotation: int):
        self.id = Prototype.prototype_count
        Prototype.prototype_count += 1
        self.name = name
        self.weight = weight
        self.face_profiles: Tuple[FaceProfile] = tuple(deepcopy(fp) for fp in face_profiles)
        self.rotation = rotation

    def getAllRotations(self, obj_face_profiles, obj) -> List[Prototype]:
        hfp = obj_face_profiles[:4]
        vfp = obj_face_profiles[4:]
        return [
            self,
            Prototype(obj.name, self.weight, tuple(rotate_list(hfp, 1) + [fp.get_rotated((fp.rotation + 1) % 4) for fp in vfp]), 1),
            Prototype(obj.name, self.weight, tuple(rotate_list(hfp, 2) + [fp.get_rotated((fp.rotation + 2) % 4) for fp in vfp]), 2),
            Prototype(obj.name, self.weight, tuple(rotate_list(hfp, 3) + [fp.get_rotated((fp.rotation + 3) % 4) for fp in vfp]), 3)
        ]

    def get_potential_neighbours(self, prototype_list: List[Prototype]):
        for i, fp in enumerate(self.face_profiles):
            if i == NZ:
                for proto in prototype_list:
                    if proto.face_profiles[PZ].id == fp.id and proto.face_profiles[PZ].rotation == fp.rotation:
                        fp.potential_neighbours.append(proto.id)
            elif i == PZ:
                for proto in prototype_list:
                    if proto.face_profiles[NZ].id == fp.id and proto.face_profiles[NZ].rotation == fp.rotation:
                        fp.potential_neighbours.append(proto.id)
            elif i == PX:
                for proto in prototype_list:
                    other = proto.face_profiles[NX]
                    if (other.id == fp.id and (not fp.flipping or fp.flipped != other.flipped)):
                        fp.potential_neighbours.append(proto.id)
            elif i == PY:
                for proto in prototype_list:
                    other = proto.face_profiles[NY]
                    if (other.id == fp.id and (not fp.flipping or fp.flipped != other.flipped)):
                        fp.potential_neighbours.append(proto.id)
            elif i == NX:
                for proto in prototype_list:
                    other = proto.face_profiles[PX]
                    if (other.id == fp.id and (not fp.flipping or fp.flipped != other.flipped)):
                        fp.potential_neighbours.append(proto.id)
            elif i == NY:
                for proto in prototype_list:
                    other = proto.face_profiles[PY]
                    if (other.id == fp.id and (not fp.flipping or fp.flipped != other.flipped)):
                        fp.potential_neighbours.append(proto.id)


# in order to make faces face each other regardless of where they are
# associate an orientation to each face profile as an offset from 0 on the unit circle * PI/2
# add the rotation of the already placed block to its face profile's rotation
# the difference of this and the other block's face profile's rotation is the rotation to give to the other block
# then flip the block (add 2 to the rotation) and place it
# this setup allows for a shortcut: add the stored rotation value to the placed block's rotation
# and use that as the to-be-placed block's rotation

class Orientation(Enum):
    EAST = 0
    NORTHEAST = 1
    NORTH = 2
    NORTHWEST = 3
    WEST = 4
    SOUTHWEST = 5
    SOUTH = 6
    SOUTHEAST = 7
    NONE = 8

def get_orientation(fpg):
    average_normal = (0, 0)
    if len(fpg) == 0:
        return (-1, -1)
    for point in fpg:
        average_normal = (average_normal[0] + point[2], average_normal[1] + point[3])
    average_normal = (average_normal[0]/len(fpg), average_normal[1]/len(fpg))
    ori_idx = int(atan2(average_normal[1], average_normal[0]) * 4 / pi)
    if ori_idx < 0: ori_idx += 8
    return Orientation(ori_idx)


def flip_orientation(ori: Orientation):
    match ori:
        case Orientation.NORTHEAST:
            return Orientation.NORTHWEST
        case Orientation.NORTHWEST:
            return Orientation.NORTHEAST
        case Orientation.EAST:
            return Orientation.WEST
        case Orientation.WEST:
            return Orientation.EAST
        case Orientation.SOUTHEAST:
            return Orientation.SOUTHWEST
        case Orientation.SOUTHWEST:
            return Orientation.SOUTHEAST
    return ori

def rot_orientation(ori: Orientation, rot_factor: int):
    if ori == Orientation.NONE:
        return Orientation.NONE
    for i in range(rot_factor):
        match ori:
            case Orientation.NORTH:
                ori = Orientation.NORTHEAST
            case Orientation.NORTHEAST:
                ori = Orientation.EAST
            case Orientation.EAST:
                ori = Orientation.SOUTHEAST
            case Orientation.SOUTHEAST:
                ori = Orientation.SOUTH
            case Orientation.SOUTH:
                ori = Orientation.SOUTHWEST
            case Orientation.SOUTHWEST:
                ori = Orientation.WEST
            case Orientation.WEST:
                ori = Orientation.NORTHWEST
            case Orientation.NORTHWEST:
                ori = Orientation.NORTH
    return ori