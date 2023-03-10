import bpy
from mathutils import Vector
from pathlib import Path
from typing import List, Tuple, Dict
from collections import Counter
from math import atan2, pi
from enum import Enum
from functools import partial

'''
hash(bpy.context.object.location.xyz.freeze())
bpy.data.collections["Prototypes"].all_objects[0].data.vertices[0].co
'''

PATH = Path('./test.txt')

objects = bpy.data.collections['Prototypes'].all_objects

file = open(PATH, 'w')

file.write('### DEBUG ###\n\n')

print('#############\n### DEBUG ###\n#############\n')

class Orientation(Enum):
    NORTH = 1
    NORTHEAST = 2
    EAST = 3
    SOUTHEAST = 4
    SOUTH = 5
    SOUTHWEST = 6
    WEST = 7
    NORTHWEST = 8
    NONE = 9

known_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]
known_vertical_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]

profile_name = 0
vertical_profile_name = 0

def get_orientation(fpg):
    average_normal = (0, 0)
    if len(fpg) == 0:
        return (-1, -1)
    print('Points:\n')
    for point in fpg:
        print(str(point) + '\n')
        average_normal = (average_normal[0] + point[2], average_normal[1] + point[3])
    average_normal = (average_normal[0]/len(fpg), average_normal[1]/len(fpg))
    print(average_normal)
    print(atan2(average_normal[1], average_normal[0])/pi)
    print('\n')
    ori_idx = int(atan2(average_normal[1], average_normal[0]) * 8 / pi)
    if ori_idx < 0: ori_idx += 8
    return Orientation(ori_idx + 1)


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

    points = [v.co[:] for v in obj.data.vertices]
    normals = [v.normal[:] for v in obj.data.vertices]

    tuple_points: List[Tuple] = [point[:] for point in points] # converts blender Vector to tuple to avoid using freeze
    tuple_normals: List[Tuple] = [normal[:] for normal in normals]

    face_profiles_geometry: Tuple[List] = ([], [], [], [])
    vertical_face_profiles_geometry: Tuple[List] = ([], [])

    face_profiles_names: List[str] = ['', '', '', '', '', '']

    for i, p in enumerate(tuple_points):
        if (p[0] == -1): # nx
            projNormals = Vector((-tuple_normals[i][1], tuple_normals[i][2], 0)).normalized()[:2]
            point_2d_proj = (-p[1], p[2], *projNormals)
            face_profiles_geometry[0].append(point_2d_proj)
        if (p[0] == +1): # px
            projNormals = Vector((tuple_normals[i][1], tuple_normals[i][2], 0)).normalized()[:2]
            point_2d_proj = (p[1], p[2], *projNormals)
            face_profiles_geometry[1].append(point_2d_proj)
        if (p[1] == -1): # ny
            projNormals = Vector((tuple_normals[i][0], tuple_normals[i][2], 0)).normalized()[:2]
            point_2d_proj = (p[0], p[2], *projNormals)
            face_profiles_geometry[2].append(point_2d_proj)
        if (p[1] == +1): # py
            projNormals = Vector((-tuple_normals[i][0], tuple_normals[i][2], 0)).normalized()[:2]
            point_2d_proj = (-p[0], p[2], *projNormals)
            face_profiles_geometry[3].append(point_2d_proj)
        if (p[2] == -1): # nz
            projNormals = Vector((tuple_normals[i][0], -tuple_normals[i][1], 0)).normalized()[:2]
            point_2d_proj = (p[0], -p[1], *projNormals)
            vertical_face_profiles_geometry[0].append(point_2d_proj)
        if (p[2] == +1): # pz
            projNormals = Vector((tuple_normals[i][0], tuple_normals[i][1], 0)).normalized()[:2]
            point_2d_proj = (p[0], p[1], *projNormals)
            vertical_face_profiles_geometry[1].append(point_2d_proj)

    for i, fpg in enumerate(face_profiles_geometry):
        if len(fpg) == 0:
            face_profiles_names[i] = '-1'
            continue
        fpg_ori = get_orientation(fpg)
        fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
        for (kfp, ori, name) in known_face_profiles:
            if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                face_profiles_names[i] = name
                break
        else:
            flipped_fpg = [(-x, y) for (x, y) in fpg]
            if Counter(fpg) == Counter(flipped_fpg) and fpg_ori == flip_orientation(fpg_ori):
                name = str(profile_name) + 's'
                known_face_profiles.append((fpg, fpg_ori, name))
                file.write('new profile found: ' + name + '\n')
            else:
                name = str(profile_name)
                known_face_profiles.append((fpg, fpg_ori, name))
                file.write('new profile found: ' + name + '\n')
                name += 'f'
                known_face_profiles.append((flipped_fpg, flip_orientation(fpg_ori), name))
                file.write('new profile found: ' + name + '\n')
            profile_name += 1

    for i, fpg in enumerate(vertical_face_profiles_geometry):
        if len(fpg) == 0:
            face_profiles_names[i] = '-1'
            continue
        fpg_ori = get_orientation(fpg)
        fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
        for (kfp, ori, name) in known_vertical_face_profiles:
            if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                face_profiles_names[i] = name
                break
        else:
            rot_1 = [(-x, y) for (x, y) in fpg]
            rot_2 = [(-x, -y) for (x, y) in fpg]
            rot_3 = [(x, -y) for (x, y) in fpg]
            name = 'v' + str(vertical_profile_name) + '_'
            if Counter(fpg) == Counter(rot_1) and Counter(fpg) == Counter(rot_2) and Counter(fpg) == Counter(rot_3):
                known_vertical_face_profiles.append((fpg, Orientation.NONE, name + 'i'))
            else:
                known_vertical_face_profiles.append((fpg, fpg_ori, name + '0'))
                known_vertical_face_profiles.append((rot_1, rot_orientation(fpg_ori, 2), name + '1'))
                known_vertical_face_profiles.append((rot_2, rot_orientation(fpg_ori, 4), name + '2'))
                known_vertical_face_profiles.append((rot_3, rot_orientation(fpg_ori, 6), name + '3'))
            vertical_profile_name += 1

# known_face_profiles = list(map(lambda fp: (list(map(lambda geo: list(map(partial(round, ndigits=5), geo)), fp[0])), fp[1]), known_face_profiles))
known_face_profiles = [([tuple(round(val, 5) for val in point) for point in geo], ori, name) for geo, ori, name in known_face_profiles]
known_vertical_face_profiles = [([tuple(round(val, 5) for val in point) for point in geo], ori, name) for geo, ori, name in known_vertical_face_profiles]

file.write('\n### DATA ###\n\n')

for fp, ori, name in known_face_profiles:
    file.write(str(fp) + ' ' + str(ori) + ' ' + name + '\n')

for fp, ori, name in known_vertical_face_profiles:
    file.write(str(fp) + ' ' + str(ori) + ' ' + name + '\n')


'''
as a rule for placement, overlapping geometry shouldn't be authorized
I need to find a way to enforce this. One way could be to add a prefix to signify that only air should be used next to this one
basically if there is a face formed by the geometry on this profile, nothing can go next to that profile
or when building everything, making sure there are no faces on the edges but this would limit variety and make everything end on a half step
this can be added later on
'''

    # file.write(str(vertices_face_profiles) + '\n')

file.close()