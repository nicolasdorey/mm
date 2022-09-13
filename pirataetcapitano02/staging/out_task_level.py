# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Maximillien Rolland
#
#   DESCRIPTION :       This tool is used to clean level before to create their bridge
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
try:
    import sgtk
    import maya.cmds as cmds
except ImportError:
    pass

from ....studio.libs.reads import references as read_references


class CleanLevelScene(object):
    def __init__(self, logger=logging):
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Grab the pre-created Sgtk instance from the current engine.
        self.tk = current_engine.sgtk
        self.sg = current_engine.shotgun
        # Log
        self.logger = logger

    def get_top_references(self):
        """
        Loop over all references of the scene and return only the top ones.
        Excluding children references, default references and trash references.
        :return: names of top reference nodes
        :rtype: list
        """
        # Loop over all references of the scene and exclude children references
        #    and trash references
        references = []
        for reference in cmds.ls(type='reference'):
            # Exclude default reference nodes
            if reference == "sharedReferenceNode":
                continue
            # Exclude "RefTrashRN" references
            if "RefTrashRN" in reference:
                continue
            # Do not process children references
            if cmds.referenceQuery(reference, parent=True, referenceNode=True):
                continue
            # Store reference
            references.append(reference)
        # Return result
        return references

    def get_parent_path(self, reference):
        """
        Return the hierarchy path of the highest node of a reference.
        :param reference: the name of the reference
        :type reference: str
        :return: hierarchy path
        :rtype: str
        """
        node = self.get_ref_top_node(reference)
        parent_path = cmds.listRelatives(node, parent=True, fullPath=True)
        if parent_path is None:
            return ''
        return parent_path[0]

    def get_path_and_namespace(self, reference):
        """
        Return path and namespace data from reference.
        :param reference: the name of the reference node
        :type reference: str
        :return: the path and the namespace of the reference
        :rtype: dict
        """
        path = cmds.referenceQuery(reference, filename=True, withoutCopyNumber=True)
        namespace = cmds.referenceQuery(reference, namespace=True)
        return {'path': path, 'namespace': namespace}

    def get_trs_data(self, transform):
        """
        Return translation, rotation and scale data.
        :param transform: the name of the transform to get trs data
        :type transform: str
        :return: translation, rotation and scale data
        :rtype: dict
        """
        translate = cmds.xform(transform, translation=True, q=True)
        rotate = cmds.xform(transform, rotation=True, query=True)
        scale = cmds.xform(transform, scale=True, relative=True, query=True)
        return {'translate': translate, 'rotate': rotate, 'scale': scale}

    def get_ref_top_node(self, reference):
        """
        Return the highest referenced node from a reference.
        :param reference: the name of the reference to get the highest node
        :type reference: str
        :return: the name of the highest node of the reference
        :rtype: str
        """
        ref_nodes = cmds.referenceQuery(reference, nodes=True, dagPath=True)
        if not ref_nodes:
            self.logger.warning('Cannot get top node of "{}" reference. Skipping it.'.format(reference))
            return None
        return ref_nodes[0]

    def get_nurbs_curves_data(self, reference):
        """
        List nurbs curves transform and return translation, rotation and scale data.
        This function returns this kind of dict:
        {
            "|OutBuildPackage_001:CaveGround01_Classic_BLD_Top|OutBuildPackage_001:RIG_Grp|OutBuildPackage_001:CaveGround01_Classic_RIG_Top|OutBuildPackage_001:Ctrls|OutBuildPackage_001:World_CtrlGrp|OutBuildPackage_001:World_Sta_CtrlGrp|OutBuildPackage_001:World_Sta_Ctrl": {
                "translate": [0.0, 18.873, 0.0],
                "rotate": [0.0, 0.0, 0.0],
                "scale": [1.5, 1.5, 1.5],
        }
        :param reference: the name of the reference node to get nurbs curves data
        :type reference: str
        :raises Exception: if no transform is found from a referenced nurbs curves
        :return: [description]
        :rtype: [type]
        """
        nurbs_curves_data = {}
        ref_nodes = cmds.referenceQuery(reference, nodes=True, dagPath=True)
        nurbs_nodes = cmds.ls(ref_nodes, exactType='nurbsCurve', long=True)
        for node in nurbs_nodes:
            transform_nodes = cmds.listRelatives(node, parent=True, fullPath=True)
            if not transform_nodes:
                raise Exception('ERROR: no transform found for shape "{}".'.format(node))
            transform = transform_nodes[0]
            nurbs_curves_data[transform] = self.get_trs_data(transform)
        return nurbs_curves_data

    def get_ref_data(self, reference):
        """
        Returns data collected of a reference as a dict.
        :param reference: the name of the reference node to get data from
        :type reference: str
        :return: reference data
        :rtype: dict
        """
        ref_data = {}
        # Store reference path and namespace
        ref_data.update(self.get_path_and_namespace(reference))
        # Check if child reference exist
        children = cmds.referenceQuery(reference, child=True, referenceNode=True)
        if children is None:
            self.logger.warning('\tNo child reference found in "{}".'.format(reference))
            return None
        # Find the active proxy reference in the children references
        child = read_references.get_active_proxy(children[0])
        # Store child reference path and namespace
        ref_data['child'] = self.get_path_and_namespace(child)
        # Store parent node of the child reference top node (to be able to create the hierarchy again)
        parent_path = self.get_parent_path(child)
        ref_data['child']['parent_path'] = parent_path
        # Store data of NURBS curves of child reference
        ref_data['child']['nurbsCurves_data'] = self.get_nurbs_curves_data(child)

        # Return result
        return ref_data

    def prepare_staging_bridge(self):
        """
        Build a dict containing data of scene references.
        This function returns this kind of dict:
        {
            "OutBuildPackage_001RN": {
                "path": "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets/CaveGround01/CaveGround01_Classic/BLD/publish/maya/CaveGround01_Classic_BLD_OutBuildPackage.v001.mb",
                "namespace": "OutBuildPackage_001",
                "child": {
                    "path": "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles/assets/CaveGround01/CaveGround01_Classic/BLD/publish/maya/CaveGround01_Classic_BLD_OutBuildCache.v002.mb",
                    "namespace": ":",
                    "nurbsCurves_data": {
                        "|OutBuildPackage_001:CaveGround01_Classic_BLD_Top|OutBuildPackage_001:RIG_Grp|OutBuildPackage_001:CaveGround01_Classic_RIG_Top|OutBuildPackage_001:Ctrls|OutBuildPackage_001:World_CtrlGrp|OutBuildPackage_001:World_Sta_CtrlGrp|OutBuildPackage_001:World_Sta_Ctrl": {
                            "translate": [0.0, 18.873, 0.0],
                            "rotate": [0.0, 0.0, 0.0],
                            "scale": [1.5, 1.5, 1.5],
                        }
                    },
                },
            },
        }
        :return: references data
        :rtype: dict
        """
        references_data = {}
        # Get parent references to store data
        references = self.get_top_references()
        # Loop over parent references to store their
        for reference in references:
            ref_data = self.get_ref_data(reference)
            if ref_data:
                references_data[reference] = ref_data
        return references_data

    def execute(self):
        self.prepare_staging_bridge()
