import bpy
from pathlib import Path
from typing import List, Tuple, Dict
from collections import Counter


'''
hash(bpy.context.object.location.xyz.freeze())
bpy.data.collections["Prototypes"].all_objects[0].data.vertices[0].co
'''

PATH = Path('./test.txt')

objects = bpy.data.collections['Prototypes'].all_objects

file = open(PATH, 'w')

known_face_profiles: List[Tuple[Tuple, str]] = []

for obj in objects:

    points = [v.co[:] for v in obj.data.vertices] 

    tuple_points: List[Tuple] = [point[:] for point in points] # converts blender Vector to tuple to avoid using freeze

    face_profiles_geometry: Tuple[List] = ([], [], [], [], [], [])

    face_profiles_names: Tuple[str] = ('', '', '', '', '', '')

    for p in tuple_points:
        if (p[0] == -1): # nx
            point_2d_proj = (-p[1], p[2])
            face_profiles_geometry[0].append(point_2d_proj)
        if (p[0] == +1): # px
            point_2d_proj = (p[1], p[2])
            face_profiles_geometry[1].append(point_2d_proj)
        if (p[1] == -1): # ny
            point_2d_proj = (p[0], p[2])
            face_profiles_geometry[2].append(point_2d_proj)
        if (p[1] == +1): # py
            point_2d_proj = (-p[0], p[2])
            face_profiles_geometry[3].append(point_2d_proj)
        if (p[2] == -1): # nz
            point_2d_proj = (p[0], -p[1])
            face_profiles_geometry[4].append(point_2d_proj)
        if (p[2] == +1): # pz
            point_2d_proj = (p[0], p[1])
            face_profiles_geometry[5].append(point_2d_proj)

    for i, fpg in enumerate(face_profiles_geometry):
        for (kfp, name) in known_face_profiles:
            if (Counter(kfp) == Counter(fpg)):
                face_profiles_names[i] = name
                break
        else:
            # todo: add check for symmetry and construct name for face profile
            pass

    # for vfp in vertices_face_profiles:
        

    # file.write(str(vertices_face_profiles) + '\n')

file.close()