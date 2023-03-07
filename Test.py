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
    normals = [v.normal[:] for v in obj.data.vertices]

    tuple_points: List[Tuple] = [point[:] for point in points] # converts blender Vector to tuple to avoid using freeze
    tuple_normals: List[Tuple] = [normal[:] for normal in normals]

    face_profiles_geometry: Tuple[List] = ([], [], [], [])
    vertical_face_profiles_geometry: Tuple[List] = ([], [])

    face_profiles_names: Tuple[str] = ('', '', '', '', '', '')

    for i, p in enumerate(tuple_points):
        if (p[0] == -1): # nx
            point_2d_proj = (-p[1], p[2], -tuple_normals[i][1], tuple_normals[i][2])
            face_profiles_geometry[0].append(point_2d_proj)
        if (p[0] == +1): # px
            point_2d_proj = (p[1], p[2], tuple_normals[i][1], tuple_normals[i][2])
            face_profiles_geometry[1].append(point_2d_proj)
        if (p[1] == -1): # ny
            point_2d_proj = (p[0], p[2], tuple_normals[i][0], tuple_normals[i][2])
            face_profiles_geometry[2].append(point_2d_proj)
        if (p[1] == +1): # py
            point_2d_proj = (-p[0], p[2], -tuple_normals[i][0], tuple_normals[i][2])
            face_profiles_geometry[3].append(point_2d_proj)
        if (p[2] == -1): # nz
            point_2d_proj = (p[0], -p[1], tuple_normals[i][0], -tuple_normals[i][1])
            vertical_face_profiles_geometry[0].append(point_2d_proj)
        if (p[2] == +1): # pz
            point_2d_proj = (p[0], p[1], tuple_normals[i][0], tuple_normals[i][1])
            vertical_face_profiles_geometry[1].append(point_2d_proj)

    for i, fpg in enumerate(face_profiles_geometry):
        for (kfp, name) in known_face_profiles:
            if (Counter(kfp) == Counter(fpg)):
                face_profiles_names[i] = name
                break
        else:
            # todo: this is where you create the different profiles if they don't exist yet
            # if i == 4 or 5, then vertical, otherwise normal.
            # remember to flip both points and normals to check
            # if flipped and unflipped are equal, name == len(known_profiles) + s and store one
            # if flipping changes, save both with f and without f
            pass

'''
as a rule for placement, overlapping geometry shouldn't be authorized
I need to find a way to enforce this. One way could be to add a prefix to signify that only air should be used next to this one
basically if there is a face formed by the geometry on this profile, nothing can go next to that profile
or when building everything, making sure there are no faces on the edges
this can be added later on
'''

    # file.write(str(vertices_face_profiles) + '\n')

file.close()