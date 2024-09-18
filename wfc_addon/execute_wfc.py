from __future__ import annotations

import bpy
import logging

from mathutils import Vector
from typing import List, Tuple
from collections import Counter
from datetime import datetime

from .wfc_utils import (
    Prototype,
    FaceProfile,
    Orientation,
    NeighbourTupleIndices as Nb,
    get_orientation,
    flip_orientation,
    rot_orientation
)
from .preferences import get_preferences
from .compute_data_operator import WFC_OT_compute_data_operator

log = logging.getLogger("wfc_addon.execute_wfc")

class WFC_OT_execute_wfc(bpy.types.Operator):
    '''Execute WFC algorithm based on computed data'''
    bl_idname = "wfc.execute_wfc"
    bl_label = "Execute WFC algorithm"

    def execute(self, context):
        prototypes: List[Prototype] = context.scene.wfc_prototypes_collection["prototypes"]

