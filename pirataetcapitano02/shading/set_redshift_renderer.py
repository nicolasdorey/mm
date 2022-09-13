# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to set Redshift Renderer for Shading workers
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

from ....studio.libs.updates import scene as update_scene


class SetRedshiftRenderer(object):
    """
    Set redshifts render settings for Shading workers
    TODO: dictionnaries should be txt files
    """
    def __init__(self, batch=True):
        # Be sure redshift renderer is loaded
        update_scene.load_plugin('redshift4maya.mll')
        logging.warning('If Redshift wasnt loaded yet, you will need to launch this tool another time')
        # Define vars
        self.renderer = 'redshift'
        self.renderer_option = 'redshiftOptions'
        self.resolution_option = 'defaultResolution'

        # Define render settings dict
        self.dict_resolution =      {
                                    'width': 1080,
                                    'height': 1080,
                                    'deviceAspectRatio': 1.778,
                                    'pixelAspect': 1.778,
                                    }

        self.dict_common_settings = {
                                    'imageFormat': 2,
                                    'pngBits': 16,
                                    }

        self.dict_output_settings = {
                                    'unifiedMinSamples': 16,
                                    'unifiedMaxSamples': 32,
                                    'unifiedFilterSize': 4,
                                    'unifiedMaxOverbright': 1,

                                    'reflectionSamplesOverrideEnable': 1,
                                    'reflectionSamplesOverrideReplace': 128,
                                    'refractionSamplesOverrideEnable': 1,
                                    'refractionSamplesOverrideReplace': 128,
                                    'lightSamplesOverrideEnable': 1,
                                    'lightSamplesOverrideReplace': 128,
                                    }

    def set_render_settings(self, renderer_option, render_settings_dict):
        """
        Set render settings of renderer by using a dictionary of settings
        """
        for current_setting in render_settings_dict:
            attr_to_set = '{}.{}'.format(renderer_option, current_setting)
            if cmds.objExists(attr_to_set):
                cmds.setAttr(attr_to_set, render_settings_dict[current_setting])
            else:
                logging.error('Attribute does not exist: "{}"!'.format(attr_to_set))


    def set_redshift_settings(self):
        # Set current renderer to Redshift and refresh render settings UI to awake redshift attributes (not a joke)
        update_scene.restore_render_settings(self.renderer)
        if cmds.window('unifiedRenderGlobalsWindow', exists=True):
            cmds.deleteUI('unifiedRenderGlobalsWindow')
        # Set render size
        self.set_render_settings(self.resolution_option, self.dict_resolution)
        logging.info('Render size has been set: {}'.format(self.dict_resolution))
        # Set common render settings
        self.set_render_settings(self.renderer_option, self.dict_common_settings)
        logging.info('Common render settings have been set: {}'.format(self.dict_common_settings))
        # Set output render settings
        self.set_render_settings(self.renderer_option, self.dict_output_settings)
        logging.info('Output render settings have been set: {}'.format(self.dict_output_settings))
