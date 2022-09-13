# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Maximillien Rolland
#                       Romain Leclerc
#
#   DESCRIPTION :       Utils for references queries
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass


# ________________________________________________________________________________________________________
# ###############################
# #--------- NAMESPACES --------#
# ###############################

# TODO: snakecase
def list_namespaces(nameFilter=None):
    """
    :param: nameFilter => None by default
    :return a list of all non default namespaces
    :rtype: list
    """
    defaults = ['UI', 'shared', 'root']
    namespaces_list = [ns for ns in cmds.namespaceInfo(
        listOnlyNamespaces=True, recurse=True) if ns not in defaults]
    namespaces_found = []

    if nameFilter is not None:
        for namespace in namespaces_list:
            if nameFilter in namespace:
                namespaces_found.append(namespace)
    else:
        namespaces_found = namespaces_list
    return namespaces_found


# TODO move it to updates - references?
def remove_ns_in_longname(node):
    """
    Remove NameSpace from long name
    :param: node
    :return: node
    :rtype: string
    """
    namespaces = list_namespaces()
    for ns in namespaces:
        if ns in node:
            node_no_ns = node.replace(ns + ":", "")
            node = node_no_ns
            return node
    return node


# ________________________________________________________________________________________________________
# ###############################
# #--------- REFERENCES --------#
# ###############################

# TODO: snakecase
def list_references(filterRef=None):
    """
    :param: filterRef => key word to match in a ref to get them
    :return a list ref in scene
    :rtype: list
    """
    ref_list = cmds.ls(rf=True)
    ref_found = []
    if filterRef is not None:
        for ref in ref_list:
            if filterRef in ref:
                ref_found.append(ref)
    else:
        ref_found = ref_list
    return ref_found


# TODO: snakecase
def get_reference_path(myReference):
    """
    :param: myReference
    :return: the path from myReference
    :rtype: string
    """
    return cmds.referenceQuery(myReference, filename=True)


# TODO: snakecase
def get_reference_dict(customFilter="*"):
    """
    :param: customFilter => "*" by default
    :return a dict with "refNode", "refFilename", "nodesInRef"
    :rtype: dict
    """
    result = []
    for ref_node in cmds.ls(customFilter, rf=True):
        result.append({'refNode': ref_node,
                       'refFilename': cmds.referenceQuery(ref_node, f=True),
                       'nodesInRef': cmds.referenceQuery(ref_node, n=True)})
    return result


# TODO: snakecase
# TODO rename "does_reference_exist"
# TODO: change code to "return os.path.exists(referencePath)" (the exists func already returns T/F)
def is_reference_exists(referencePath):
    """
    :param: referencePath
    :return: True or False if file exists or not
    :rtype: boolean
    """
    if not os.path.exists(referencePath):
        return False
    else:
        return True


def get_reference_infos():
    """
    Return all ref with their path and check if file exists or not
    :return: dict_to_return => {reference:[referencePath, bool]}
    :rtype: dict
    """
    refs_in_scene_list = list_references()
    dict_to_return = {}
    for ref_found in refs_in_scene_list:
        # Reset list
        ref_infos_list = []
        # Put ref path in list
        ref_path = get_reference_path(ref_found)
        ref_infos_list.append(ref_path)
        # Put exist or not in list
        ref_infos_list.append(is_reference_exists(ref_path))
        # Put list in dict
        dict_to_return[ref_found] = ref_infos_list
    return dict_to_return


# ________________________________________________________________________________________________________
# ###############################
# #---------- PROXY ------------#
# ###############################

# Used in this file
def get_proxy_manager(reference_node, logger=logging):
    """
    :param: reference_node
    :return: proxy_manager[0] or None
    :rtype: string or boolean
    """
    proxy_manager = cmds.listConnections(reference_node + '.proxyMsg', source=True, destination=False)
    if proxy_manager:
        return proxy_manager[0]
    logger.warning('No proxy manager node find for "{}" reference.'.format(reference_node))
    return None


# Used in build_bridge_level
def get_active_proxy(proxy_node):
    """
    :param: proxy_node
    :return: list of proxy_destination connections
    :rtype: list
    """
    proxy_manager = get_proxy_manager(proxy_node)
    proxy_destination = cmds.listConnections(proxy_manager + '.activeProxy', plugs=True)
    return cmds.listConnections(proxy_destination[0], source=False)


# Unused
def is_active_proxy(reference_node, proxy):
    """
    :param: reference_node
    :param: proxy
    :return: active_proxy in proxies
    """
    proxy_manager = get_proxy_manager(reference_node)
    proxies = cmds.listConnections(proxy + '.proxyMsg', plugs=True)
    active_proxy = cmds.listConnections(proxy_manager + '.activeProxy', plugs=True)[0]
    return active_proxy in proxies


# Unused
def get_proxy_from_tag(reference_node, tag):
    """
    :param: reference_node
    :param: tag
    :return: proxy or None
    :rtype: string or boolean
    """
    proxy_manager = get_proxy_manager(reference_node)
    proxy_cons = cmds.getAttr(proxy_manager + '.proxyList', multiIndices=True)
    proxies = []
    for connection in proxy_cons:
        proxy = cmds.listConnections('{}.proxyList[{}]'.format(proxy_manager, connection),
                                     destination=True, source=False)
        if proxy is not None:
            proxies.append(proxy[0])
    for proxy in proxies:
        proxy_tag = cmds.getAttr(proxy + '.proxyTag')
        if proxy_tag == tag:
            return proxy
    return None
