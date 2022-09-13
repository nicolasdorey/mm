# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for layers updates
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         glob var problem in found_maya_scene. Unfound rendersetup
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
try:
    import maya.cmds as cmds
    import maya.app.renderSetup.model.renderSetup as renderSetup

except ImportError:
    pass


from ..reads import layers as read_layers


# TODO: return the list of layers that have been unlocked
# TODO: it will interesting to have this unique method to lock/unlock display layers
# TODO: rename: lock_display_layers, put lock statement as arg => lock_display_layers(lock=True)
# TODO: snakecase
def unlock_display_layers():
    """
    Unlock non default display layers
    """
    all_display_layers = read_layers.list_display_layers()
    if all_display_layers:
        for display_layer in all_display_layers:
            if cmds.getAttr(display_layer + '.displayType') != 0:
                cmds.setAttr(display_layer + '.displayType', 0)
                logging.info('"{}" has been unlocked.'.format(display_layer))
            else:
                logging.info('"{}" was already unlocked.'.format(display_layer))
    else:
        logging.warning('No Display Layer to unlock.')


# Unused
# TODO: return the list of deleted layers
# TODO: put a list of render layers to delete and delete all layers if list is None
# TODO: don't put an empty list as arg, we want to be able to delete an empty list instead of all renderlayers
def clean_render_layers():
    """
    Delete non default renderLayer setup and legacy
    """
    # Clean Layers Setup
    render_layer_setup = renderSetup.instance()
    render_layer_setup.clearAll()
    logging.info('Setup Render Layers have been successfully cleaned.')
    # Delete render layers
    for render_layer in read_layers.list_render_layers():
        if render_layer != 'defaultRenderLayer':
            cmds.delete(render_layer)
            logging.info('Render Layers have been successfully deleted.')
