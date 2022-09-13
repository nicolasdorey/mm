# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#   AUTHOR :            Theodoric "KrNNN" JUILLET and Audrey LECSO
#
#   DESCRIPTION :       Create a root and a walk for an object. Can setup both parent and skin version.
#
#   Update  1.0.0 :     We start here.
#           1.1.0 :     Now using matrix, invert mesh for object flipping (Maya only), add layers creation, replace tabs with spaces.
#
#   KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

try:
    import maya.cmds as cmds
except ImportError:
    pass


def create_grp_hie(base_name, sh_color, rad):
    ctrl = cmds.circle(n="{}_ctrl".format(base_name), nr=(0, 1, 0), c=(0, 0, 0), r=rad)
    cmds.rename(ctrl[1], "{}_ctrlForm".format(base_name))
    cmds.group(n="{}_pos_grp".format(base_name))
    cmds.group(n="{}_inf_grp".format(base_name))
    group = cmds.group(n="{}_offset_grp".format(base_name))
    cmds.setAttr("{}Shape.overrideEnabled".format(ctrl[0]), 1)
    cmds.setAttr("{}Shape.overrideColor".format(ctrl[0]), sh_color)
    return (group, ctrl[0])


def create_rig(create_skeleton=True):
    geo_grp = cmds.ls('Geo_grp')
    existing_rig = cmds.ls('MotionSystem_grp', 'Skeleton_grp')
    if geo_grp and not existing_rig:
        geo_bbox = cmds.xform(geo_grp, bb=True, q=True)
        rad = max(abs(geo_bbox[0]), abs(geo_bbox[2]), abs(geo_bbox[3]), abs(geo_bbox[5])) * 1.5
        root = create_grp_hie(base_name='Root', sh_color=4, rad=rad * 1.2)
        walk = create_grp_hie(base_name='Walk', sh_color=22, rad=rad)
        cmds.parent(walk[0], root[1])
        cmds.select(root[0])
        motion_sys_grp = cmds.group(n="MotionSystem_grp")
        if create_skeleton:
            cmds.select(d=True)
            root_jnt = cmds.joint(n="Root_jnt", p=(0, 0, 0))
            skeleton_grp = cmds.group(n="Skeleton_grp")
            mesh_list = cmds.listRelatives(geo_grp, ad=True, type='mesh', f=True)
            for shape in mesh_list:
                mesh = cmds.listRelatives(shape, p=True, f=True)[0]
                if len([
                        elem for elem in cmds.listConnections(
                            cmds.listRelatives(
                                mesh, c=True, type='mesh', f=True))
                        if cmds.objectType(elem) == 'skinCluster'
                ]) <= 0:
                    cmds.skinCluster(root_jnt, mesh, n=mesh.split('|')[-1].replace(mesh.split('_')[-1], 'scl'), tsb=True)
                    tweak = [
                        elem for elem in cmds.listConnections(
                            cmds.listRelatives(
                                mesh, c=True, type='mesh', f=True))
                        if cmds.objectType(elem) == 'tweak'
                    ]
                    cmds.rename(
                        tweak,
                        mesh.split('|')[-1].replace(
                            mesh.split('_')[-1], 'twk'))
            dcp_node = cmds.shadingNode('decomposeMatrix', n=walk[1].replace(walk[1].split('_')[-1], 'dcpmtx'), asUtility=True)
            cmds.connectAttr('{}.worldMatrix[0]'.format(walk[1]), '{}.inputMatrix'.format(dcp_node))
            cmds.connectAttr('{}.outputTranslate'.format(dcp_node), '{}.translate'.format(root_jnt))
            cmds.connectAttr('{}.outputRotate'.format(dcp_node), '{}.rotate'.format(root_jnt))
            cmds.connectAttr('{}.outputScale'.format(dcp_node), '{}.scale'.format(root_jnt))
        else:
            cmds.parentConstraint(walk[1], geo_grp)
            cmds.scaleConstraint(walk[1], geo_grp)

        cmds.select(skeleton_grp)
        cmds.createDisplayLayer(noRecurse=True, name='Skeleton_lay')
        cmds.select(cl=True)
        cmds.select(motion_sys_grp)
        cmds.createDisplayLayer(noRecurse=True, name='MotionSystem_lay')
        cmds.select(cl=True)
        cmds.select(geo_grp)
        cmds.createDisplayLayer(noRecurse=True, name='Geo_lay')
        cmds.select(cl=True)

        cmds.select(d=True)
        cmds.warning(
            "--- Done ! Please edit both Walk_ctrlForm and Root_ctrlForm Radius in input shape to fit the object size (Root in Red, walk in Yellow). ---"
        )
    elif not geo_grp:
        cmds.warning(
            "--- No Geo_grp detected, please check and try again ! ---")
    elif existing_rig:
        cmds.warning(
            "--- There is already a rig in the scene, skipping... ---")


if __name__ == "__main__":
    create_rig()
