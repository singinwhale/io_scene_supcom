import pathlib
from typing import List

import bpy
import bpy.props
import bmesh
import bmesh.ops
import mathutils

from bpy_extras.io_utils import ExportHelper, orientation_helper, axis_conversion
from bpy.types import Operator, Context
from mathutils import Matrix

from PySupComIO.model import Model, Bone, Vertex, Triangle
import PySupComIO.write.model

@orientation_helper(axis_forward='X', axis_up='Y')
class ExportScmOperator(Operator, ExportHelper):
    triangulate_quad_method: bpy.props.EnumProperty(
        items=[
            ('BEAUTY', "Beauty ", "Split the quads in nice triangles, slower method"),
            ('FIXED', "Fixed", "Split the quads on the first and third vertices"),
            ('FIXED_ALTERNATE', "Fixed Alternate", "Split the quads on the 2nd and 4th vertices"),
            ('SHORTEST_DIAGONAL', "Shortest Diagonal", "Split the quads based on the distance between the vertices")
        ],
        default='BEAUTY',
        name="Quad triangulation method",
        description="How should blender triangulate quads on the mesh",
    )

    triangulate_ngon_method: bpy.props.EnumProperty(
        items=[
            ('BEAUTY', "Beauty ", "Arrange the new triangles evenly (slow)"),
            ('CLIP', "CLIP", "Split the polygons with an ear clipping algorithm")
        ],
        default='BEAUTY',
        name="N-gon triangulation method",
        description="How should blender triangulate n-gons on the mesh",
    )

    info_string: bpy.props.StringProperty(
        name="Info String",
        description="String that is put into the info section of the mesh",
        default=""
    )

    export_object: bpy.types.Object = None
    bm: bmesh.types.BMesh = None
    armature: bpy.types.Armature = None
    scm: Model = None

    def invoke(self, context, event):
        return super().invoke(context, event)

    def check(self, context):
        return super().check(context)

    def execute(self, context: Context):
        # TODO: we should probably export from the armature down
        #  and merge all children which are skinned to it by merging the objects into one bmesh

        self.export_object = context.active_object
        self.bm = bmesh.new()
        self.bm.from_mesh(self.export_object.data)

        self.armature = context.active_object.data  # todo figure out where to get the armature from

        self.scm = Model()
        self.scm.name = self.armature
        self.scm.info = self.info_string

        self.set_bones()
        self.set_geometry()

        PySupComIO.write.model.write_model(self.scm, pathlib.Path(self.filepath))

    def set_bones(self):
        conversion_matrix = self.get_axis_conversion_matrix()

        bones: List[bpy.types.Bone] = self.armature.bones

        assert bones[0].parent is None, "First bone is assumed to be the root bone!"

        for ix, blender_bone in enumerate(bones):
            bone_transform_relative_to_origin: Matrix = conversion_matrix @ blender_bone.matrix_local
            bone_local_rotation_matrix = blender_bone.matrix

            scm_bone = Bone()
            scm_bone.name = blender_bone.name
            scm_bone.index = ix
            scm_bone.parent_index = bones.index(blender_bone.parent)
            # TODO: this will  not work for the root bone
            scm_bone.transform.rotation = list(bone_local_rotation_matrix.to_quaternion())
            scm_bone.transform.position = list(blender_bone.parent.tail_local)
            scm_bone.inverse_rest_pose_matrix = bone_transform_relative_to_origin.inverted()

            self.scm.bones.append(scm_bone)

    def set_geometry(self):
        conversion_matrix = self.get_axis_conversion_matrix()

        self.triangulate()
        self.bake_smoothness()

        vertex_dict = dict()
        vertices = []
        triangles = []

        skin_vert_layers = self.bm.verts.layers.skin

        for blender_vertex in self.bm.verts:
            blender_vertex.normal_update()

            scm_vertex = Vertex()

            scm_vertex.index = blender_vertex.index
            scm_vertex.position = conversion_matrix @ blender_vertex.co
            scm_vertex.normal = conversion_matrix@blender_vertex.normal
            scm_vertex.UVs = self.get_uvs_from_vertex(blender_vertex)
            scm_vertex.bones = self.get_bone_indexes_from_vertex(blender_vertex)
            # todo: use MikkTSpace technique to generate normal and binormal from UVs, or get them from the face?
            scm_vertex.binormal = None
            scm_vertex.tangent = None

            vertices.append(scm_vertex)

        for blender_face in self.bm.faces:
            vertex_index_list = list([blender_vertex.index for blender_vertex in blender_face.verts])
            assert len(vertex_index_list) == 3
            scm_triangle = Triangle()
            scm_triangle.vertex_indexes = vertex_index_list
            triangles.append(vertex_index_list)

        self.scm.vertices = vertices
        self.scm.faces = triangles


    def get_axis_conversion_matrix(self) -> Matrix:
        conversion_matrix = axis_conversion(to_forward=self.axis_forward, to_up=self.axis_up)
        return conversion_matrix

    def triangulate(self):
        edges, faces, face_map, face_map_double = bmesh.ops.triangulate(
            self.bm,
            faces=self.bm.faces,
            quad_method=self.triangulate_quad_method,
            ngon_method=self.triangulate_ngon_method
        )

    def bake_smoothness(self):
        sharp_edges = set()

        # find all flat shaded faces and mark all their edges as sharp
        for face in self.bm.faces:
            if not face.smooth:
                for edge in face.edges:
                    edge.smooth = False

        # find all explicitly sharp edges
        # sharp edges are separate from smooth faces and a smooth/sharp face does not set its edges to sharp/smooth
        for edge in self.bm.edges:
            is_sharp = not edge.smooth
            if is_sharp:
                sharp_edges.add(edge.index)

        bmesh.ops.split_edges(self.bm, edges=sharp_edges, use_verts=False)

    def get_uvs_from_vertex(self, blender_vertex):
        vertex_uvs = dict()
        for name, uv_layer in self.bm.loops.layers.uv.items():
            for loop in blender_vertex.link_loops:
                if uv_layer not in vertex_uvs:
                    vertex_uvs[uv_layer] = set()

                vertex_uvs[uv_layer].add(loop[uv_layer].uv)

        UVs = []
        for uv_layer, uv_set in vertex_uvs:
            if len(uv_set) == 0:
                raise Exception(f"Vertex {blender_vertex.index} is not unwrapped on uvlayer {uv_layer.name}")

            # todo we can fix this if we  do the splitting by code but retain the old vertex normal
            #  which would allow us to have smooth shaded faces with a UV split in between and no hassle while editing
            if len(uv_set) != 1:
                raise Exception(f"Vertex {blender_vertex.index} has multiple uv coordinates on UVLayer {uv_layer.name} "
                                f"which means that it is part of multiple uv islands. "
                                f"Please split the edge")

            # add the single vector from the uvs to the model as a list
            UVs.append(list(next(iter(uv_set))))
        return UVs

    def get_bone_indexes_from_vertex(self, blender_vertex):
        deform_layer = self.bm.verts.layers.deform.active  # '' is the only deform layer there can ever be
        deform_vert = blender_vertex[deform_layer]

        if len(deform_vert.items()) > 4:
            raise Exception(f"Vertex {blender_vertex.index} is skinned to more than 4 bones")

        armature_bones = self.armature.bones
        bone_indexes = []
        for group_index, weight in deform_vert.items():
            bone_name = self.export_object.vertex_groups[group_index]
            bone_index = armature_bones[bone_name]
            bone_indexes.append(bone_index)

        return bone_indexes
