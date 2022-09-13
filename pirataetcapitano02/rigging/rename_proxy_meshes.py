# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       ?
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError as e:
    pass

from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.checks import nodes as check_nodes

# FIXME: waiting for tk-multi-sanitycheck
from ...Common.common.sanity_checks import sanity_check_rigging

# TODO: if there is a check and a rename, we should put them  in checks and updates libraries!
# This tool is not really a tool


def check_and_rename_meshes():
    """
    Rename meshes that are badly names
    """
    sc = sanity_check_rigging.SanityCheckRigging()
    if not sc.check_meshes_nom():
        all_meshes = read_nodes.list_all_meshes()
        for mesh in all_meshes:
            if not check_nodes.check_obj_nomenclature(mesh):
                if check_nodes.check_valide_suffix(mesh, regexp=r'_\d\d$'):
                    mesh = rename_mesh(mesh, 3)

                elif check_nodes.check_valide_suffix(mesh, regexp=r'_\d$'):
                    mesh = rename_mesh(mesh, 2)

                else:
                    logging.error('aucun des deux')


def rename_mesh(mesh, digits):
    """
    Renames meshes from number of digits found
    """
    logging.info('*' * 100)
    mesh_sn = cmds.ls(mesh, sn=True)
    if mesh_sn:
        mesh_sn = mesh_sn[0]
        new_name = mesh_sn[:-digits]

        try:
            new_name = cmds.rename(mesh, new_name)
            logging.info('The mesh {} has been renamed to {}'.format(mesh, new_name))
        except Exception as e:
            logging.error('{} Could not rename mesh {}'.format(e, mesh))
    return new_name
