from __future__ import annotations
import bpy
from mathutils import Vector
import json
from typing import List, Tuple
from collections import Counter
from wfc_utils import *
import logging

log = logging.getLogger("wfc_addon.compute_data_operator")

class WFC_OT_compute_data_operator(bpy.types.Operator):
    '''Compute setup data to transfer to Unity'''
    bl_idname = "wfc.compute_data_operator"
    bl_label = "Compute WFC Data"
    prototypes: List[Prototype] = []


    def execute(self, context):
        file = open(LOG_PATH, 'w') if context.scene.WFC_log_data else None
        def log_message(message):
            if (context.scene.WFC_log_data):
                file.write(message)

        log_message('#############\n### DEBUG ###\n#############\n\n')

        objects = context.scene.WFC_prototypes_collection.all_objects

        known_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]
        known_vertical_face_profiles: List[Tuple[List[Tuple], Orientation, str]] = [([], Orientation.NONE, '-1')]

        profile_id = 0

        prototypes: List[Prototype] = [
            Prototype("-1", 1, (FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1), FaceProfile(-1)), -1)
        ] # first prototype is empty

        for obj in objects:

            log_message(obj.name + '\n')

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
                    log_message('Identified empty horizontal face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                    continue
                fpg_ori = get_orientation(fpg)
                fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
                for (kfp, ori, ofp) in known_face_profiles:
                    if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                        obj_face_profiles[i] = ofp
                        log_message('Identified horizontal face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                        break
                else:
                    flipped_fpg = [(-x, y) for (x, y) in fpg]
                    if Counter(fpg) == Counter(flipped_fpg) and fpg_ori == flip_orientation(fpg_ori):
                        ofp = FaceProfile(profile_id, False, False)
                        known_face_profiles.append((fpg, fpg_ori, ofp))
                        known_face_profiles.append((flipped_fpg, fpg_ori, ofp))
                        obj_face_profiles[i] = ofp
                        log_message('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
                    else:
                        ofp = FaceProfile(profile_id, False, True, False)
                        known_face_profiles.append((fpg, fpg_ori, ofp))
                        obj_face_profiles[i] = ofp
                        log_message('new profile found: ' + str(ofp) + ' ' + str(fpg_ori) + '\n')
                        ofp = FaceProfile(profile_id, False, True, True)
                        known_face_profiles.append((flipped_fpg, flip_orientation(fpg_ori), ofp))
                        log_message('new profile found: ' + str(ofp) + ' ' + str(flip_orientation(fpg_ori)) + '\n')
                    profile_id += 1

            # Create/Associate vertical face profiles
            for i, fpg in enumerate(vertical_face_profiles_geometry):
                i += 4
                if len(fpg) == 0:
                    obj_face_profiles[i] = FaceProfile(-1, True)
                    log_message('Identified empty vertical face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
                    continue
                fpg_ori = get_orientation(fpg)
                fpg = [(x, y) for (x, y, nx, ny) in fpg] # discarding normals as we now have orientation
                for (kfp, ori, ofp) in known_vertical_face_profiles:
                    if (Counter(kfp) == Counter(fpg) and ori == fpg_ori):
                        obj_face_profiles[i] = ofp
                        log_message('Identified vertical face profile at ' + str(i) + ': ' + str(obj_face_profiles[i]) + '\n')
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
                        log_message('new profile found: ' + str(ofp) + '\n')
                    else:
                        ofp = FaceProfile(profile_id, True, True, 0)
                        obj_face_profiles[i] = ofp
                        log_message('new profiles found: ' + str(ofp) + ', 1, 2, 3\n')
                        known_vertical_face_profiles.append((fpg, fpg_ori, ofp))
                        known_vertical_face_profiles.append((rot_1, rot_1_ori, FaceProfile(profile_id, True, True, 1)))
                        known_vertical_face_profiles.append((rot_2, rot_2_ori, FaceProfile(profile_id, True, True, 2)))
                        known_vertical_face_profiles.append((rot_3, rot_3_ori, FaceProfile(profile_id, True, True, 3)))
                    profile_id += 1
            log_message('\n')
            hfp = obj_face_profiles[:4]
            vfp = obj_face_profiles[4:]
            log_message('Face profiles: ' + str([str(fp) for fp in obj_face_profiles]) + '\n')
            weight: float = obj.get("Weight", 1.0)
            obj["Weight"] = float(weight)
            proto = Prototype(obj.name, weight, tuple(obj_face_profiles), 0)
            prototypes += proto.getAllRotations(obj_face_profiles, obj)

        for proto in prototypes:
            proto.get_potential_neighbours(prototypes)
        WFC_OT_compute_data_operator.prototypes = prototypes
        for p in prototypes:
            p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
        data = [p.__dict__ for p in prototypes]
        context.scene.WFC_prototypes_collection["prototypes"] = data
        log.info("Computed data")
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
        log.info("Dumped debug data to log.txt")

    def create_json(self):
        prototypes = WFC_OT_compute_data_operator.prototypes
        with open(JSON_DATA_PATH, "w") as json_file:
            for p in prototypes:
                p.face_profiles = tuple(fp.__dict__ for fp in p.face_profiles)
            data = [p.__dict__ for p in prototypes]
            data_wrapper = {"data": data}
            json.dump(data_wrapper, json_file, indent=2)
        log.info("Wrote JSON data to data.json")
