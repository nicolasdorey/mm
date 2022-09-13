# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to set Redshift Attr for Shading workers
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.updates import nodes as update_scene
from ....studio.libs.reads import nodes as read_nodes


class SetRedshiftAttr(object):
    """
    Set redshifts attr
    - On selection if exists
    - Or on all related elements
    """
    def __init__(self, batch=True):
        # Be sure redshift renderer is loaded
        update_scene.load_plugin('redshift4maya.mll')
        # Set var
        self.geo_shapes_list = cmds.ls(geometry=True)
        self.files_list = cmds.ls(type='file')
        self.is_batch = batch
        # Set attr dict
        self.dict_smooth_attr = {
            'displaySmoothMesh': 0,
            'rsEnableSubdivision': 1,
            'rsSubdivisionRule': 0,
            'rsMaxTessellationSubdivs': 3,
            'rsScreenSpaceAdaptive': 1,
            'rsDoSmoothSubdivision': 1,
            'rsMinTessellationLength': 1,
            'rsOutOfFrustumTessellationFactor': 2,
        }
        self.dict_file_attr = {
            'rsFilterEnable': 0,
        }

    def open_confirmation_popup(self, node_type):
        """
        Load redshift plugin in not already loaded
        """
        confirm = cmds.confirmDialog(title='Confirm', message='No selection found, apply on all {}?      '.format(node_type), button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        return confirm

    def set_rs_on_shapes(self, selection=[]):
        """
        Set redshift attributs on geometry shapes
        If set attr failed, put shapes in a list and return it
        """
        ok_attr = []
        error_attr = []
        list_of_shapes = []
        # If no selection, get all shapes in scene or abort
        if not selection:
            if not self.is_batch:
                confirm = self.open_confirmation_popup('shapes')
                if confirm == 'No':
                    logging.warning('Process aborted.')
                    return
            list_of_shapes = self.geo_shapes_list
        # Else get shapes from selection
        else:
            for node_found in selection:
                if cmds.objectType(node_found) == 'mesh':
                    list_of_shapes.append(node_found)
                else:
                    list_of_geo = read_nodes.get_recursive_meshes(node_found)
                    for transform_found in list_of_geo:
                        list_of_shapes.append(read_nodes.get_shape_or_transform(transform_found))
            # Clean list
            list_of_shapes = list(set(list_of_shapes))

        # Apply attr on selected shapes
        for shape_found in list_of_shapes:
            for smooth_attr in self.dict_smooth_attr:
                attr_to_set = '{}.{}'.format(shape_found, smooth_attr)
                try:
                    cmds.setAttr(attr_to_set, self.dict_smooth_attr.get(smooth_attr))
                    ok_attr.append(attr_to_set)
                except Exception as e:
                    logging.error('ERROR: {}'.format(e))
                    error_attr.append(attr_to_set)
        # Logs
        if ok_attr:
            logging.info('List of Redshift attribut that have been set: "{}"'.format(ok_attr))
        if error_attr:
            logging.error('List of Redshift attribut that cannot be set: "{}"'.format(error_attr))

        return error_attr

    def set_rs_on_files(self, selection=[]):
        """
        Set redshift attributs on files
        If set attr failed, put files in a list and return it
        """
        error_files = []
        # If no selection, get all files in scene or abort
        if not selection:
            if not self.is_batch:
                confirm = self.open_confirmation_popup('files')
                if confirm is False:
                    logging.warning('Process aborted.')
                    return
            selection = self.files_list
        # Apply attr on selected files
        for file_found in selection:
            try:
                for file_attr in self.dict_file_attr:
                    cmds.setAttr('{}.{}'.format(file_found, file_attr), self.dict_file_attr.get(file_attr))
                logging.info('Redshift attributs have been set on file: "{}"'.format(file_found))
            except Exception:
                logging.error('Redshift attributs cannot be set on geometry file: "{}"'.format(file_found))
                error_files.append(file_found)

        return error_files
