def menu_func(self, context):


# self.layout.operator(EXPORT_OT_scm.bl_idname, text="Supcom Mesh (.scm)")
# self.layout.operator(EXPORT_OT_sca.bl_idname, text="Supcom Anim (.sca)")


# ===========================================================================
# Entry
# ===========================================================================
def register():


# print("REGISTER")
# bpy.utils.register_class(EXPORT_OT_sca)
# bpy.utils.register_class(EXPORT_OT_scm)
# bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():


# print("UNREGISTER")
# bpy.utils.unregister_class(EXPORT_OT_sca)
# bpy.utils.unregister_class(EXPORT_OT_scm)
# bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    # print("\n"*4)
    # print(header("SupCom Export scm/sca 4.0", 'CENTER'))
    register()
