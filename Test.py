from __future__ import annotations
import bpy
from mathutils import Vector
from copy import copy
from pathlib import Path
import json
from typing import List, Tuple, Dict
from collections import Counter
from math import atan2, pi
from enum import Enum
# from functools import partial

PATH = Path('./test.txt')

file = open(PATH, 'w')

file.write('### DEBUG ###\n\n')

print('#############\n### DEBUG ###\n#############\n')

objects = bpy.data.collections['Prototypes'].all_objects

# Tuple indices for neighbour association
PX = 0
PY = 1
NX = 2
NY = 3
NZ = 4
PZ = 5

class FaceProfile:
    def __init__(self, uid: int, vertical: bool = False, rotating: bool = False, rotation: int = 0) -> None:
        self.id = uid
        self.vertical = vertical
        self.rotating = rotating
        self.flipping = rotating
        self.rotation = rotation
        self.flipped = bool(rotation)

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

class Prototype:
    prototype_count = 0

    def __init__(self, name: str, face_profiles: Tuple[FaceProfile]):
        self.id = Prototype.prototype_count
        Prototype.prototype_count += 1
        self.name = name
        self.face_profiles: Tuple[FaceProfile] = face_profiles
        self.potential_neighbours: Tuple[List[Tuple[int, int]]] = ([], [], [], [], [], [])

    def get_potential_neighbours(self, prototype_list: List[Prototype]):
        for i, fp in enumerate(self.face_profiles):
            if i == NZ:
                for proto in prototype_list:
                    if proto.face_profiles[PZ].id == fp.id:
                        self.potential_neighbours[NZ].append((proto.id, fp.rotation))
            elif i == PZ:
                for proto in prototype_list:
                    if proto.face_profiles[NZ].id == fp.id:
                        self.potential_neighbours[PZ].append((proto.id, fp.rotation))
            else:
                for proto in prototype_list:
                    for j, other in enumerate(proto.face_profiles):
                        if (other.vertical): continue
                        if fp.id == other.id and (not fp.flipping or fp.flipped != other.flipped):
                            self.potential_neighbours[i].append((proto.id, (i - j + 2) % 4))

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

known_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]
known_vertical_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]

profile_id = 0

prototypes: List[Prototype] = [
    Prototype("-1", (FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1)))
] # first prototype is empty

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


for obj in objects:

    file.write(obj.name + '\n')
    print(obj.name)

    points = [v.co.to_tuple(5) for v in obj.data.vertices]
    normals = [v.normal.to_tuple(5) for v in obj.data.vertices]

    face_profiles_geometry: Tuple[List] = ([], [], [], [])
    vertical_face_profiles_geometry: Tuple[List] = ([], [])

    obj_face_profiles: List[FaceProfile] = [FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1)]

    # Sort points into face profiles
    for p, n in zip(points, normals):
        if (p[0] == -1): # nx
            projNormals = Vector((-n[1], n[2], 0)).normalized()[:2]
            point_2d_proj = (-p[1], p[2], *projNormals)
            face_profiles_geometry[NX].append(point_2d_proj)
        if (p[0] == +1): # px
            projNormals = Vector((n[1], n[2], 0)).normalized()[:2]
            point_2d_proj = (p[1], p[2], *projNormals)
            face_profiles_geometry[PX].append(point_2d_proj)
        if (p[1] == -1): # ny
            projNormals = Vector((n[0], n[2], 0)).normalized()[:2]
            point_2d_proj = (p[0], p[2], *projNormals)
            face_profiles_geometry[NY].append(point_2d_proj)
        if (p[1] == +1): # py
            projNormals = Vector((-n[0], n[2], 0)).normalized()[:2]
            point_2d_proj = (-p[0], p[2], *projNormals)
            face_profiles_geometry[PY].append(point_2d_proj)
        if (p[2] == -1): # nz
            projNormals = Vector((n[0], -n[1], 0)).normalized()[:2]
            point_2d_proj = (p[0], -p[1], *projNormals)
            vertical_face_profiles_geometry[0].append(point_2d_proj)
        if (p[2] == +1): # pz
            projNormals = Vector((n[0], n[1], 0)).normalized()[:2]
            point_2d_proj = (p[0], p[1], *projNormals)
            vertical_face_profiles_geometry[1].append(point_2d_proj)

    # Create/Associate horizontal face profiles
    for i, fpg in enumerate(face_profiles_geometry):
        if len(fpg) == 0:
            continue
        fpg_ori = get_orientation(fpg)
        fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
        for (kfp, ori, ofp) in known_face_profiles:
            if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                obj_face_profiles[i] = copy(ofp)
                break
        else:
            flipped_fpg = [(-x, y) for (x, y) in fpg]
            if Counter(fpg) == Counter(flipped_fpg) and fpg_ori == flip_orientation(fpg_ori):
                ofp = FaceProfile(profile_id, False, False)
                known_face_profiles.append((fpg, fpg_ori, ofp))
                file.write('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
            else:
                ofp = FaceProfile(profile_id, False, True, False)
                known_face_profiles.append((fpg, fpg_ori, ofp))
                file.write('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
                ofp = FaceProfile(profile_id, False, True, True)
                known_face_profiles.append((flipped_fpg, flip_orientation(fpg_ori), ofp))
                file.write('new profile found: ' + str(ofp) + ' ' + str(flip_orientation(fpg_ori)) + '\n')
            profile_id += 1

    # Create/Associate vertical face profiles
    for i, fpg in enumerate(vertical_face_profiles_geometry):
        if len(fpg) == 0:
            obj_face_profiles[i] = FaceProfile(-1, True)
            continue
        fpg_ori = get_orientation(fpg)
        fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
        for (kfp, ori, ofp) in known_vertical_face_profiles:
            if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                obj_face_profiles[i] = copy(ofp)
                break
        else:
            rot_1, rot_1_ori = ([(-x, y) for (x, y) in fpg], rot_orientation(fpg_ori, 2))
            rot_2, rot_2_ori = ([(-x, -y) for (x, y) in fpg], rot_orientation(fpg_ori, 4))
            rot_3, rot_3_ori = ([(x, -y) for (x, y) in fpg], rot_orientation(fpg_ori, 6))
            if Counter(fpg) == Counter(rot_1) and Counter(fpg) == Counter(rot_2) and Counter(fpg) == Counter(rot_3)\
            and fpg_ori == rot_1_ori and fpg_ori == rot_2_ori and fpg_ori == rot_3_ori:
                ofp = FaceProfile(profile_id, True, False)
                known_vertical_face_profiles.append((fpg, Orientation.NONE, ofp))
                file.write('new profile found: ' + str(ofp) + '\n')
            else:
                ofp = FaceProfile(profile_id, True, True, 0)
                file.write('new profiles found: ' + str(ofp) + ', 1, 2, 3\n')
                known_vertical_face_profiles.append((fpg, fpg_ori, ofp))
                known_vertical_face_profiles.append((rot_1, rot_1_ori, FaceProfile(profile_id, True, True, 1)))
                known_vertical_face_profiles.append((rot_2, rot_2_ori, FaceProfile(profile_id, True, True, 2)))
                known_vertical_face_profiles.append((rot_3, rot_3_ori, FaceProfile(profile_id, True, True, 3)))
            profile_id += 1
    file.write('\n')
    prototypes.append(Prototype(obj.name, tuple(obj_face_profiles)))

for proto in prototypes:
    proto.get_potential_neighbours(prototypes)

file.write('\n### DATA ###\n\n')

for fp, ori, ofp in known_face_profiles:
    file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

file.write('\n')

for fp, ori, ofp in known_vertical_face_profiles:
    file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

file.write('\n')

for proto in prototypes:
    file.write(proto.name + '\n')
    for (fp, pn) in zip(proto.face_profiles, proto.potential_neighbours):
        file.write(str(fp) + '\n')
        file.write(str(pn) + '\n')
    file.write('\n')

with open("data.json", "w") as json_file:
    for p in prototypes:
        p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
    data = [p.__dict__ for p in prototypes]
    json.dump(data, json_file, indent=2)

'''
as a rule for placement, overlapping geometry shouldn't be authorized
I need to find a way to enforce this. One way could be to add a prefix to signify that only air should be used next to this one
basically if there is a face formed by the geometry on this profile, nothing can go next to that profile
or when building everything, making sure there are no faces on the edges but this would limit variety and make everything end on a half step
this can be added later on
'''

file.close()