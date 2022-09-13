# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used to create level
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         WIP: this tool does not import assembly placement (shavar) but multiple sub assets (parent variation)
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging

try:
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import references as read_references


class BuildBridgeLevelScene(object):
    def __init__(self, logger=logging):
        self.logger = logger

    def exclude_empty_string(self, string_list):
        """
        Return a list without empty strings
        :param string_list: list of string to exclude empty strings from
        :type string_list: list
        :return: the input list of string without empty strings
        :rtype: list
        """
        result = []
        for item in string_list:
            if item != '':
                result.append(item)
        return result

    def load_as_reference(self, path, namespace):
        """Load as reference a file in the current Maya scene.

        :param path: the reference file path
        :type path: str
        :param namespace: the namespace to use
        :type namespace: str
        :return: references nodes
        :rtype: list
        """
        return cmds.file(path,
                         reference=True,
                         mergeNamespacesOnClash=False,
                         namespace=namespace,
                         returnNewNodes=True)

    def get_parent_reference_node(self, nodes):
        """
        Return the first parent reference node found in a list of reference nodes.
        :param nodes: reference node names
        :type nodes: list
        :return: parent reference node name
        :rtype: str
        """
        ref_nodes = cmds.ls(nodes, references=True)
        for node in ref_nodes:
            if cmds.referenceQuery(node, referenceNode=True, parent=True) is None:
                return node

    def get_proxy_top_node(self, proxy):
        """
        Return the top node of a proxy reference node
        :param proxy: reference node name
        :type proxy: str
        :return: top node name
        :rtype: str
        """
        proxy_nodes = cmds.referenceQuery(proxy, nodes=True, dagPath=True)
        return proxy_nodes[0]

    def rebuild_hierarchy(self, proxy, parent_path):
        """
        Build a hierarchy and put the top node of a reference inside
        :param proxy: reference node name
        :type proxy: str
        :param parent_path: Maya hierarchy path (using "|" like long names)
        :type parent_path: str
        """
        # 1. Get the top node of the child reference
        proxy_top_node = self.get_proxy_top_node(proxy)

        # 2. Create hierarchy
        nodes_from_path = parent_path.split('|')
        nodes_from_path = self.exclude_empty_string(nodes_from_path)
        last_node = ''
        for node in nodes_from_path:
            new_node_long_name = '{}|{}'.format(last_node, node)
            if not cmds.objExists(new_node_long_name):
                new_node = cmds.createNode('transform', name=node, parent=last_node)
            else:
                new_node = node
            last_node = '{}|{}'.format(last_node, new_node)

        # 3. Parent nodes
        cmds.parent(proxy_top_node, last_node)

    def set_trs(self, top_node, trs_data):
        """
        Set translate, rotate and scale values to node.
        :param top_node: node name
        :type top_node: str
        :param trs_data: translate, rotate and scale values
        :type trs_data: dict
        :raises Exception: if no transform is connected to a shape
        :return: the result of the set as True or False
        :rtype: bool
        """
        new_nodes = cmds.listRelatives(top_node, allDescendents=True, fullPath=True)
        nurbs_nodes = cmds.ls(new_nodes, exactType='nurbsCurve', long=True)
        for node in nurbs_nodes:
            transform = cmds.listRelatives(node, parent=True, fullPath=True)

            if not transform:
                raise Exception('ERROR: no transform found for shape "{}".'.format(node))
            transform = transform[0]

            if transform not in trs_data:
                self.logger.warning('\tCannot find "{}" in child data NURBS curves. Skipping it.'.format(transform))
                return False
            cmds.xform(transform,
                       translation=trs_data[transform]['translate'],
                       rotation=trs_data[transform]['rotate'],
                       scale=trs_data[transform]['scale'])
        return True

    def get_children_references(self, reference):
        """
        Return children references from a reference node
        :param reference: reference node name
        :type reference: str
        :return: children references nodes names
        :rtype: list
        """
        children = cmds.referenceQuery(reference, child=True, referenceNode=True)
        if children is None:
            self.logger.warning('\tNo child reference found in "{}"'.format(reference))
            return None
        return children

    def get_child_data(self, reference_data, reference_node_name):
        """
        Check and return "child" value from the input dictionary.
        :param reference_data: reference information
        :type reference_data: dict
        :param reference_node_name: reference node name
        :type reference_node_name: str
        :return: child reference information
        :rtype: dict
        """
        if 'child' not in reference_data:
            self.logger.warning('\tCannot find child reference of "{}". Skipping it.'.format(reference_node_name))
            return None
        return reference_data['child']

    def rebuild_reference(self, reference_node_name, reference_data):
        """
        Use reference data dict to create reference in current scene.
        :param reference_node_name: the reference node name
        :type reference_node_name: str
        :param reference_data: reference information
        :type reference_data: dict
        :return: None if fails one step
        :rtype: NoneType
        """
        # Load as reference with the path and the namespace
        new_nodes = self.load_as_reference(reference_data['path'], reference_data['namespace'])
        # Get parent reference node just created
        reference = self.get_parent_reference_node(new_nodes)
        # Get child reference data
        child_data = self.get_child_data(reference_data, reference_node_name)
        if child_data is None:
            return None
        # Get children of loaded reference
        children = self.get_children_references(reference)
        if children is None:
            return None
        # Get the active proxy of the loaded reference
        active_proxy = read_references.get_active_proxy(children[0])
        # Compare the active proxy with the child reference data to see if switch is needed
        proxy_path = cmds.referenceQuery(active_proxy[0], filename=True, withoutCopyNumber=True)
        if proxy_path != child_data['path']:
            self.logger.warning('\tExpected "{}" and have "{}". Need to switch proxy!'.format(child_data['path'], proxy_path))
            return None

        # Parent the top node of the child reference to the right hierarchy
        self.rebuild_hierarchy(active_proxy, child_data['parent_path'])
        # Get the top node of the child reference with new hierarchy path
        proxy_top_node = self.get_proxy_top_node(active_proxy)
        # Loop over child reference NURBS curves and apply transform values of the dict
        self.set_trs(proxy_top_node, child_data['nurbsCurves_data'])

    def build_scene(self, references_data):
        """
        Generate scene from dict containing references data.
        This dict is generated by "out_task_level.CleanLevelScene().prepare_staging_bridge()"
        :param references_data: [description]
        :type references_data: [type]
        """
        # Generate scene from references_data dict.
        #   This dict contains references path, namespace and child reference path and namespaces.
        #   Also, there is NURBS curves translate, scale and rotate info in child references data.*
        for ref_node_name, ref_data in references_data.iteritems():

            # Rebuild each reference
            self.rebuild_reference(ref_node_name, ref_data)
        self.logger.info('Build scene done!')
