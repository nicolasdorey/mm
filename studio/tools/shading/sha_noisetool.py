# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Theodoric Juillet
#
#   DESCRIPTION :       Apply material with preseted noise on selected objects.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import maya.cmds as cmds
except ImportError:
    pass


def create_materials():
    meshes = cmds.ls(sl=True, type='transform')
    if meshes:
        for mesh in meshes:
            mesh = mesh.replace('_msh', '')
            mesh = mesh.split(':')[-1]
            shader_check = cmds.ls("{}_Mat".format(mesh))
            if not shader_check:
                shader = cmds.shadingNode('RedshiftMaterial', asShader=True, n="{}_Mat".format(mesh))
                cmds.setAttr("{}.refl_weight".format(shader), 1)
                cmds.setAttr("{}.refl_roughness".format(shader), .35)

                shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, n="{}_SG".format(mesh))
                cmds.connectAttr("{}.outColor".format(shader), "{}.surfaceShader".format(shading_group), f=True)
                cmds.connectAttr("{}.outColor".format(shader), "{}.rsSurfaceShader".format(shading_group), f=True)

                noise = cmds.shadingNode('RedshiftNoise', asShader=True, n="{}_Nse".format(mesh))
                cmds.setAttr("{}.coord_scale_global".format(noise), 5)
                for scale in range(3):
                    cmds.setAttr("{}.coord_scale{}".format(noise, scale), 1)
                cmds.connectAttr("{}.outColor".format(noise), "{}.diffuse_color".format(shader), f=True)

                bump = cmds.shadingNode('RedshiftBumpMap', asShader=True, n="{}_Bmp".format(mesh))
                cmds.setAttr("{}.factorInObjScale".format(bump), 0)
                cmds.setAttr("{}.scale".format(bump), .1)
                cmds.connectAttr("{}.out".format(bump), "{}.bump_input".format(shader), f=True)
                cmds.connectAttr("{}.outColor".format(noise), "{}.input".format(bump), f=True)

                mesh_full_name = cmds.ls("*{}_msh".format(mesh), r=True)[0]
                cmds.select("{}".format(mesh_full_name), r=True)
                cmds.sets(e=True, fe=shading_group)
                cmds.setAttr("{}Shape.vertexColorSource".format(mesh_full_name), 0)

                cmds.skinCluster("{}".format(mesh_full_name), edit=True, unbind=True)
            else:
                cmds.warning("--- Shader already existing, skiping... ---")
        cmds.warning('--- Shaders succesfully created ! ---')

        # rs_mesh_parameters_check = cmds.ls('Geo_rsMeshParameters', r=True)
        # if not rs_mesh_parameters_check:
        #     rs_mesh_parameters = cmds.shadingNode('RedshiftMeshParameters',
        #                                           asShader=True,
        #                                           n="Geo_rsMeshParameters")
        #     for mesh in meshes:
        #         mesh_full_name = cmds.ls("*{}_msh".format(mesh), r=True)[0]
        #         cmds.sets(mesh_full_name, e=True)
        #     else:
        #         cmds.warning("--- RsMeshParameters  ---")

    else:
        cmds.warning("--- Selection is empty, aborting... ---")
