import bpy
from pathlib import Path
from typing import List, Tuple, Dict
from collections import Counter
from mathutils import Vector

'''
hash(bpy.context.object.location.xyz.freeze())
bpy.data.collections["Prototypes"].all_objects[0].data.vertices[0].co
'''

PATH = Path('./test.txt')

objects = bpy.data.collections['Prototypes'].all_objects

file = open(PATH, 'w')

known_face_profiles: List[Tuple[Tuple, str]] = [([], '-1')]
known_vertical_face_profiles: List[Tuple[Tuple, str]] = [([], '-1')]

for obj in objects:

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
        for (kfp, name) in known_face_profiles:
            if (Counter(kfp) == Counter(fpg)):
                face_profiles_names[i] = name
                break
        else:
            flipped_fpg = [(-x, y, -nx, ny) for (x, y, nx, ny) in fpg]
            if Counter(fpg) == Counter(flipped_fpg):
                name = str(len(known_face_profiles)) + 's'
                known_face_profiles.append((fpg, name))
            else:
                name = str(len(known_face_profiles))
                known_face_profiles.append((fpg, name))
                name += 'f'
                known_face_profiles.append((flipped_fpg, name))

    for i, fpg in enumerate(vertical_face_profiles_geometry):
        for (kfp, name) in known_vertical_face_profiles:
            if (Counter(kfp) == Counter(fpg)):
                face_profiles_names[i] = name
                break
        else:
            rot_1 = [(-x, y, -nx, ny) for (x, y, nx, ny) in fpg]
            rot_2 = [(-x, -y, -nx, -ny) for (x, y, nx, ny) in fpg]
            rot_3 = [(x, -y, nx, -ny) for (x, y, nx, ny) in fpg]
            name = 'v' + str(len(known_vertical_face_profiles)) + '_'
            if (Counter(fpg) == Counter(rot_1) and Counter(fpg) == Counter(rot_2) and Counter(fpg) == Counter(rot_3)):
                known_vertical_face_profiles.append((fpg, name + 'i'))
            else:
                known_vertical_face_profiles.append((fpg, name + '0'))
                known_vertical_face_profiles.append((rot_1, name + '1'))
                known_vertical_face_profiles.append((rot_2, name + '2'))
                known_vertical_face_profiles.append((rot_3, name + '3'))

for fp, name in known_face_profiles:
    file.write(str(fp) + ' ' + name + '\n')

for fp, name in known_vertical_face_profiles:
    file.write(str(fp) + ' ' + name + '\n')


'''
as a rule for placement, overlapping geometry shouldn't be authorized
I need to find a way to enforce this. One way could be to add a prefix to signify that only air should be used next to this one
basically if there is a face formed by the geometry on this profile, nothing can go next to that profile
or when building everything, making sure there are no faces on the edges
this can be added later on
'''

    # file.write(str(vertices_face_profiles) + '\n')

file.close()