from __future__ import annotations
import bpy
from mathutils import Vector
from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path
import json
from typing import List, Tuple, Dict
from collections import Counter
from math import atan2, pi
from enum import Enum
import logging
# from functools import partial

bl_info = {
    "name": "Wave Function Collapse Setup",
    "author": "Primarter",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Edit Panel > WFC Setup",
    "description": "Sets up objects to be used in Unity with a Wave Function Collapse algorithm",
    "warning": "",
    "doc_url": "",
    "category": "Setup WFC",
}

LOG_PATH = bpy.path.abspath('//log.txt')
DUMP_DATA_PATH = bpy.path.abspath('//dump.txt')
JSON_DATA_PATH = bpy.path.abspath('//data.json')

log = logging.getLogger(__name__)

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

class WFC_OT_compute_data_operator(bpy.types.Operator):
    '''Compute setup data to transfer to Unity'''
    bl_idname = "wfc.compute_data_operator"
    bl_label = "Compute WFC Data"
    prototypes = []

    def execute(self, context):
        file = open(LOG_PATH, 'w')

        file.write('### DEBUG ###\n\n')

        print('#############\n### DEBUG ###\n#############\n')

        objects = context.scene.WFC_prototypes_collection.all_objects

        known_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]
        known_vertical_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]

        profile_id = 0

        prototypes: List[Prototype] = [
            Prototype("-1", 1, (FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1)), -1)
        ] # first prototype is empty

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
                    obj_face_profiles[i] = FaceProfile(-1, True)
                    # file.write('Identified empty horizontal face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                    continue
                fpg_ori = get_orientation(fpg)
                fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
                for (kfp, ori, ofp) in known_face_profiles:
                    if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                        obj_face_profiles[i] = ofp
                        # file.write('Identified horizontal face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                        break
                else:
                    flipped_fpg = [(-x, y) for (x, y) in fpg]
                    if Counter(fpg) == Counter(flipped_fpg) and fpg_ori == flip_orientation(fpg_ori):
                        ofp = FaceProfile(profile_id, False, False)
                        known_face_profiles.append((fpg, fpg_ori, ofp))
                        known_face_profiles.append((flipped_fpg, fpg_ori, ofp))
                        obj_face_profiles[i] = ofp
                        file.write('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
                    else:
                        ofp = FaceProfile(profile_id, False, True, False)
                        known_face_profiles.append((fpg, fpg_ori, ofp))
                        obj_face_profiles[i] = ofp
                        file.write('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
                        ofp = FaceProfile(profile_id, False, True, True)
                        known_face_profiles.append((flipped_fpg, flip_orientation(fpg_ori), ofp))
                        file.write('new profile found: ' + str(ofp) + ' ' + str(flip_orientation(fpg_ori)) + '\n')
                    profile_id += 1

            # Create/Associate vertical face profiles
            for i, fpg in enumerate(vertical_face_profiles_geometry):
                i += 4
                if len(fpg) == 0:
                    obj_face_profiles[i] = FaceProfile(-1, True)
                    # file.write('Identified empty vertical face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                    continue
                fpg_ori = get_orientation(fpg)
                fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
                for (kfp, ori, ofp) in known_vertical_face_profiles:
                    if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                        obj_face_profiles[i] = ofp
                        # file.write('Identified vertical face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                        break
                else:
                    rot_1, rot_1_ori = ([(-x, y) for (x, y) in fpg], rot_orientation(fpg_ori, 2))
                    rot_2, rot_2_ori = ([(-x, -y) for (x, y) in fpg], rot_orientation(fpg_ori, 4))
                    rot_3, rot_3_ori = ([(x, -y) for (x, y) in fpg], rot_orientation(fpg_ori, 6))
                    if Counter(fpg) == Counter(rot_1) and Counter(fpg) == Counter(rot_2) and Counter(fpg) == Counter(rot_3)\
                    and fpg_ori == rot_1_ori and fpg_ori == rot_2_ori and fpg_ori == rot_3_ori:
                        ofp = FaceProfile(profile_id, True, False)
                        known_vertical_face_profiles.append((fpg, Orientation.NONE, ofp))
                        obj_face_profiles[i] = ofp
                        file.write('new profile found: ' + str(ofp) + '\n')
                    else:
                        ofp = FaceProfile(profile_id, True, True, 0)
                        obj_face_profiles[i] = ofp
                        file.write('new profiles found: ' + str(ofp) + ', 1, 2, 3\n')
                        known_vertical_face_profiles.append((fpg, fpg_ori, ofp))
                        known_vertical_face_profiles.append((rot_1, rot_1_ori, FaceProfile(profile_id, True, True, 1)))
                        known_vertical_face_profiles.append((rot_2, rot_2_ori, FaceProfile(profile_id, True, True, 2)))
                        known_vertical_face_profiles.append((rot_3, rot_3_ori, FaceProfile(profile_id, True, True, 3)))
                    profile_id += 1
            file.write('\n')
            hfp = obj_face_profiles[:4]
            vfp = obj_face_profiles[4:]
            # file.write('Face profiles: ' + str([str(fp) for fp in obj_face_profiles]) + '\n')
            weight: float = obj.get("Weight", 1.0)
            obj["Weight"] = float(weight)
            proto = Prototype(obj.name, weight, tuple(obj_face_profiles), 0)
            prototypes += proto.getAllRotations(obj_face_profiles, obj)

        for proto in prototypes:
            proto.get_potential_neighbours(prototypes)
        WFC_OT_compute_data_operator.prototypes = prototypes
        return {'FINISHED'}

    def debug_data(self):
        prototypes = WFC_OT_compute_data_operator.prototypes
        file = open(DUMP_DATA_PATH, 'a')
        file.write('### DATA ###\n\n')

        # for fp, ori, ofp in known_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        # for fp, ori, ofp in known_vertical_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        for proto in prototypes:
            file.write(proto.name + ' ' + str(proto.id) + '\n')
            for fp in proto.face_profiles:
                file.write(str(fp) + '\n')
                # file.write(str(fp.potential_neighbours) + '\n')
            file.write('\n')

    def create_json(self):
        prototypes = WFC_OT_compute_data_operator.prototypes
        with open(JSON_DATA_PATH, "w") as json_file:
            for p in prototypes:
                p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
            data = [p.__dict__ for p in prototypes]
            data_wrapper = {"data": data}
            json.dump(data_wrapper, json_file, indent=2)

'''
Rotation is made through swizzling the sides
'''

class WFC_OT_dump_data(bpy.types.Operator):
    '''Dump data to text file'''
    bl_idname = "wfc.dump_data"
    bl_label = "Dump WFC data to text file"

    def execute(self, context):
        prototypes = WFC_OT_compute_data_operator.prototypes
        file = open(DUMP_DATA_PATH, 'a')
        file.write('\n### DATA ###\n\n')

        # for fp, ori, ofp in known_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        # for fp, ori, ofp in known_vertical_face_profiles:
        #     file.write(str(fp) + ' ' + str(ori) + ' ' + str(ofp) + '\n')

        # file.write('\n')

        for proto in prototypes:
            file.write(proto.name + ' ' + str(proto.id) + '\n')
            for fp in proto.face_profiles:
                file.write(str(fp) + '\n')
                # file.write(str(fp.potential_neighbours) + '\n')
            file.write('\n')
        return {'FINISHED'}

class WFC_OT_create_json(bpy.types.Operator):
    '''Dump data to a JSON file for transfer to Unity'''
    bl_idname = "wfc.create_json"
    bl_label = "Dump WFC data to JSON file"

    def execute(self, context):
        prototypes = WFC_OT_compute_data_operator.prototypes
        with open(JSON_DATA_PATH, "w") as json_file:
            for p in prototypes:
                p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
            data = [p.__dict__ for p in prototypes]
            data_wrapper = {"data": data}
            json.dump(data_wrapper, json_file, indent=2)
        return {'FINISHED'}

class WFC_OT_clear_data(bpy.types.Operator):
    '''Clear setup data'''
    bl_idname = "wfc.clear_data"
    bl_label = "Clear WFC data"

    def execute(self, context):
        print(context.scene.WFC_prototypes_collection)
        return {'FINISHED'}

class WFC_OT_create_weight(bpy.types.Operator):
    '''Create custom property Weight on current object'''
    bl_idname = "wfc.create_weight"
    bl_label = "Create Weight"

    def execute(self, context):
        context.object['Weight'] = float(1.0)
        return {'FINISHED'}

class WFC_OT_print_operator(bpy.types.Operator):
    '''Print selected collection'''
    bl_idname = "wfc.print_operator"
    bl_label = "Minimal Operator"

    def execute(self, context):
        print(context.scene.WFC_prototypes_collection)
        return {'FINISHED'}

class WFC_PT_wfc_panel(bpy.types.Panel):
    '''This panel is used to setup the data needed for the Wave Function Collapse algorithm'''
    bl_label = "WFC Setup"
    bl_idname = "WFC_PT_wfc_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Edit"

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Collection to setup:")
        layout.prop(context.scene, "WFC_prototypes_collection", text="")
        layout.separator()
        col = layout.column()
        col.label(text="Current Object:" )
        if (len(context.selected_objects) > 0 and context.selected_objects[0].get('Weight') is not None):
            col.label(text=context.selected_objects[0].name)
            col.prop(context.object, '["Weight"]')
        else:
            col.operator(WFC_OT_create_weight.bl_idname, text="Create Weight prop")
            col.enabled = len(context.selected_objects) > 0
        layout.separator()
        layout.operator(WFC_OT_compute_data_operator.bl_idname, text="Compute Data")
        layout.operator(WFC_OT_dump_data.bl_idname, text="Dump Data")
        layout.operator(WFC_OT_create_json.bl_idname, text="Create JSON File")
        

def register():
    bpy.types.Scene.WFC_prototypes_collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.utils.register_class(WFC_OT_create_weight)
    bpy.utils.register_class(WFC_OT_compute_data_operator)
    bpy.utils.register_class(WFC_OT_dump_data)
    bpy.utils.register_class(WFC_OT_create_json)
    bpy.utils.register_class(WFC_PT_wfc_panel)


def unregister():
    bpy.utils.unregister_class(WFC_PT_wfc_panel)
    bpy.utils.unregister_class(WFC_OT_create_json)
    bpy.utils.unregister_class(WFC_OT_dump_data)
    bpy.utils.unregister_class(WFC_OT_compute_data_operator)
    bpy.utils.unregister_class(WFC_OT_create_weight)
    del bpy.types.Scene.WFC_prototypes_collection


if __name__ == "__main__":
    register()

# TODO add options to panel (paths, debug to file or console, do that by adding properties like the collection)
# Check if it works, hopefully it does
# add purging data button and data status
# add buttons for dumping etc
# add weight setup button
# switch back to static variables for prototypes to be able to dump
# display custom data Weight in panel?