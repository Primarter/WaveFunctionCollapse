import bpy
from pathlib import Path
from typing import List, Tuple, Dict


'''
hash(bpy.context.object.location.xyz.freeze())
bpy.data.collections["Prototypes"].all_objects[0].data.vertices[0].co
'''

PATH = Path('D:/Github/BlenderScripting/test.txt')

objects = bpy.data.collections['Prototypes'].all_objects

file = open(PATH, 'w')

for obj in objects:

    points = [v.co[:] for v in obj.data.vertices] 

    comparisons = (
        lambda p: p[0] == -1, # nx
        lambda p: p[0] == +1, # px
        lambda p: p[1] == -1, # ny
        lambda p: p[1] == +1, # py
        lambda p: p[2] == -1, # nz
        lambda p: p[2] == +1, # pz
    )

    tuple_points: List[Tuple] = [point[:] for point in points] # converts blender Vector to tuple to avoid using freeze

    face_profiles: Tuple[List] = ([], [], [], [], [], [])

    for p in tuple_points:
        for i, comp in enumerate(comparisons):
            if comp(p):
                face_profiles[i].append(p)

    file.write(str(face_profiles) + '\n')

file.close()