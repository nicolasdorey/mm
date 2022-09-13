
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for shaders updates
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

from ..reads import shaders as read_shaders


# Used in sha_module_connections
# NOTE: Function with same name found in sanity_check_network
def rename_shading_network(shader, asset_name, variation_name, shader_name, extra_name, logger=logging):
    """
    Go throught shading network to replace names by current scene values
    :param: shader, asset_name, variation_name, shader_name, extra_name
    :return: returned_nodes
    :rtype: list
    """
    returned_nodes = []

    template = "{}_{}_{}"
    template_shader = "{}_{}_{}_{}"
    shading_network = read_shaders.get_shading_network([shader])
    shading_network.append(shader)
    string_to_search = template.format("AssetName", "VariationName", "ExtraName")
    string_shader = template_shader.format("AssetName", "VariationName", "ShaderName", "ExtraName")

    # Go through shading network to rename
    for node in shading_network:
        if string_to_search or string_shader in node:
            if string_shader in node:
                string_replaced = template_shader.format(asset_name, variation_name, shader_name, extra_name)
                new_node_name = node.replace(string_shader, string_replaced)
            else:
                string_replaced = template.format(asset_name, variation_name, extra_name)
                new_node_name = node.replace(string_to_search, string_replaced)

            if node != new_node_name:
                try:
                    cmds.rename(node, new_node_name)
                    returned_nodes.append(new_node_name)
                    logger.info('node {} has been renamed to : {} \n'.format(node, new_node_name))
                except Exception as e:
                    logger.warning("{}  // Couldnt rename node {} !".format(e, node))

    return returned_nodes
