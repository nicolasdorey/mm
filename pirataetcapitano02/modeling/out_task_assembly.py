# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#
#   DESCRIPTION :       This tool is used conform modeling assemblies
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

from . import detect_sym_auto
from ....studio.libs.reads import nodes as read_nodes
from ....studio.libs.updates import nodes as update_nodes
from ....studio.libs.updates import references as update_references

# FIXME IMPORT THEM WHEN MOVED OR FROM TK-MULTI-SANITYCHECK
from ....Common.common.sanity_checks import sanity_check


class RenameAssemblyNodes(object):
    """
    This script will rename topnodes by using the detect sym auto
    """
    def __init__(self):
        # Get the engine instance that is currently running.
        current_engine = sgtk.platform.current_engine()
        # Grab the pre-created Sgtk instance from the current engine.
        self.tk = current_engine.sgtk
        self.sg = current_engine.shotgun
        current_context = current_engine.context
        assembly_name = current_context.entity.get('name')
        step_name = current_context.step.get('name')
        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        shotgun_read_steps = fw_shotgun.import_module('studio.libs.reads.steps')
        step_sn = shotgun_read_steps.get_step_short_name(self.sg, step_name)
        # Set self var
        self.modeling_step_sn = 'MDL'
        self.topnode_suffixe = 'Top'
        self.sym_auto_sets = ['CTRL_MATCH_SYMETRY', 'CTRL_UNIQUE', 'CTRL_C', 'CTRL_POTENTIAL_SELFSYM']
        self.grp_suffixe = 'Grp'
        self.unique_prefix = 'U'
        self.center_prefix = 'C'
        self.left_prefix = 'L'
        self.right_prefix = 'R'
        self.subassets_group = 'Subassets_Grp'
        self.assembly_top_node = '{}_{}_{}'.format(assembly_name, step_sn, self.topnode_suffixe)
        self.name_dict = {}
        self.modeling_note = {}
        self.axis = ['X', 'Y', 'Z']
        self.transforms = ['translate', 'rotate', 'scale']

    def rename_topnode(self, sub_topnodes):
        """
        Rename topnode and remove namespace
        Replace _Top suffixe by _Grp suffixe
        Add prefix letter
        """
        buffer_sub_topnodes = []
        # Remove namespace
        for sub_topnode in sub_topnodes:
            sub_topnode_list = sub_topnode.split(':')
            if not len(sub_topnode_list) >= 1:
                raise Exception("Couldn't extract 1 namespace from sub_topnode `{}`. Aborting.".format(sub_topnode))
            nonamespace_sub_topnode = sub_topnode_list[1]
            # Store sub topnode shortname in a list to identify multiples subs
            buffer_sub_topnodes.append(nonamespace_sub_topnode)
            merged_old_name = "".join(nonamespace_sub_topnode.split("_")[0:2])
            new_name = "{}_{}{:02d}_{}".format(self.unique_prefix, merged_old_name, buffer_sub_topnodes.count(nonamespace_sub_topnode), self.grp_suffixe)
            cmds.rename(sub_topnode, new_name)
            logging.info('The node "{}" has been renamed "{}"'.format(sub_topnode, new_name))
            # Store new name
            self.name_dict[sub_topnode] = new_name

    def remove_namespace(self):
        """
        Remove namespaces from other nodes
        """
        nodes_to_rename = cmds.ls('*:*')
        for node_found in nodes_to_rename:
            if cmds.objExists(node_found):
                nonamespace_node = node_found.split(':')[1]
                cmds.rename(node_found, nonamespace_node)
                # Update new name in stored dict
                self.store_new_name(node_found, nonamespace_node)

        logging.info('Namespaces has been removed from meshes and sub groups names.')

    def update_prefix_letter(self):
        """
        Rename prefix from sym auto sets
        """
        for set_found in self.sym_auto_sets:
            # We don't use CTRL_POTENTIAL_SELFSYM as we are not sure it is really symetrical,
            # CTRL_UNIQUE is the default statement use for sub topnode renaming (prefix U)
            if cmds.objExists(set_found):
                if set_found != 'CTRL_POTENTIAL_SELFSYM' and set_found != 'CTRL_UNIQUE':
                    set_content = cmds.ls(cmds.listConnections(set_found), l=True)
                    logging.info('Looking for "{}" content: {}'.format(set_found, set_content))
                    content_parent_dict = {}
                    # Identify nodes from set and their parents
                    for content_element in set_content:
                        content_topnode = content_element.split('|')[2]
                        if not content_parent_dict.get(content_topnode):
                            content_parent_dict[content_topnode] = [content_element]
                        else:
                            content_elements_list = content_parent_dict.get(content_topnode) + [content_element]
                            content_parent_dict[content_topnode] = content_elements_list
                    logging.info('Parent dict from "{}" content: {}'.format(set_found, content_parent_dict))
                    # Rename centered topnode from CTRL_C set
                    if set_found == 'CTRL_C':
                        for content_parent in content_parent_dict:
                            new_content_parent = content_parent.replace('{}_'.format(self.unique_prefix), '{}_'.format(self.center_prefix))
                            cmds.rename(content_parent, new_content_parent)
                            # Update new name in stored dict
                            self.store_new_name(content_parent, new_content_parent)
                    # Rename centered topnode from CTRL_MATCH_SYMETRY set
                    elif set_found == 'CTRL_MATCH_SYMETRY':
                        # Need to know if topnode has to be renamed C_ or R/L_
                        for content_parent in content_parent_dict:
                            if content_parent_dict.get(content_parent):
                                if len(content_parent_dict.get(content_parent)) > 1:
                                    new_content_parent = content_parent.replace('{}_'.format(self.unique_prefix), '{}_'.format(self.center_prefix))
                                elif len(content_parent_dict.get(content_parent)) == 1:
                                    if cmds.getAttr('{}.translateX'.format(content_parent)) < 0:
                                        new_content_parent = content_parent.replace('{}_'.format(self.unique_prefix), '{}_'.format(self.right_prefix))
                                    else:
                                        new_content_parent = content_parent.replace('{}_'.format(self.unique_prefix), '{}_'.format(self.left_prefix))
                                cmds.rename(content_parent, new_content_parent)
                                # Update new name in stored dict
                                self.store_new_name(content_parent, new_content_parent)

    def store_new_name(self, old_name, new_name):
        for key, value in self.name_dict.items():
            if old_name == value:
                self.name_dict[key] = new_name

    def create_modeling_note(self):
        for key, value in self.name_dict.items():
            asset_dict = {}
            transform_dict = {}
            # Store old name
            old_name_no_ns = key.split(':')[-1]
            asset_dict['old_name'] = old_name_no_ns
            asset_name = old_name_no_ns.split('_{}'.format(self.modeling_step_sn))[0]
            # Store new name
            asset_longname = cmds.ls(value, l=True)
            if not asset_longname:
                return
            asset_ln = asset_longname[0]
            asset_dict['new_name'] = asset_ln
            # Store transforms
            for transform in self.transforms:
                for axe in self.axis:
                    transform_axe = '{}{}'.format(transform, axe)
                    transform_value = cmds.getAttr('{}.{}'.format(asset_ln, transform_axe))
                    transform_dict[transform_axe] = transform_value
            asset_dict['transform'] = transform_dict

            if self.modeling_note.get(asset_name):
                asset_dict_list = self.modeling_note.get(asset_name) + [asset_dict]
            else:
                asset_dict_list = [asset_dict]
            self.modeling_note[asset_name] = asset_dict_list

    def get_negatives_transforms(self):
        """
        Get transforms with negatives values
        """
        all_groups = read_nodes.list_all_groups()
        transforms_dict = read_nodes.get_transform_info(all_groups)
        negative_transforms = []
        for mesh, transf in transforms_dict.items():
            scale = transf['s']
            for scale_axis in scale:
                if scale_axis < 0:
                    negative_transforms.append(mesh)

        if negative_transforms:
            negative_transforms = list(dict.fromkeys(negative_transforms))
            logging.info('Negatives transforms found : {}'.format(negative_transforms))
            return negative_transforms

    def clean_negatives_transforms(self):
        """
        Freeze negatives transforms and reverse child normals
        """
        transform_to_freeze = self.get_negatives_transforms()
        if not transform_to_freeze:
            return transform_to_freeze

        for transf in transform_to_freeze:
            cmds.makeIdentity(transf, apply=True, t=1, r=1, s=1, n=0, pn=True)  # add preserve normal True to avoid reversed normals
            children = read_nodes.get_recursive_meshes(transf)

            for child in children:
                if not read_nodes.is_group(child):
                    # utils_nodes.reverse_normals(child) # useless with preserve normals
                    cmds.delete(child, constructionHistory=True)
                    logging.info('Faces have been reversed to : {}'.format(child))

        return transform_to_freeze

    def freeze_and_clean(self):
        """
        Freeze transform and delete history
        """
        assembly_topnode = read_nodes.get_top_node()
        nodes_to_freeze = cmds.listRelatives(assembly_topnode[0], f=True, c=True)
        for sub_top_node in nodes_to_freeze:
            cmds.delete(sub_top_node, constructionHistory=True)
            cmds.makeIdentity(sub_top_node, apply=True, t=1, r=1, s=1, n=0)
        logging.info('All topnodes have been freezed and their history deleted.')

    def clean_sets(self):
        """
        Clean selection sets from sym auto and log any other set found
        """
        selection_sets = read_nodes.non_default_nodes_only(cmds.ls(set=True))
        for set_found in selection_sets:
            if set_found not in self.sym_auto_sets:
                logging.error('An unauthorized set has been found in assembly scene: {}'.format(set_found))
            cmds.sets(cl=set_found)
            cmds.delete(set_found)
        logging.info('Selection sets has been deleted.')

    # -----------------------------------------------------------------------------------------------

    def execute(self):
        # Flat references
        update_references.remove_reference(deleteRef=False)
        # Get sub topnodes list
        sub_topnodes = cmds.ls('*:*_{}'.format(self.topnode_suffixe))
        logging.info('Sub topnodes list: {}'.format(sub_topnodes))
        # Remove namespaces and rename topnodes
        self.rename_topnode(sub_topnodes)
        # Remove namespaces from other nodes
        self.remove_namespace()
        # Detect sym auto and update prefix letter
        detect_sym_auto.compare_all_meshes()
        detect_sym_auto.check_u_sym()
        self.update_prefix_letter()
        # Rename assembly topnode
        cmds.rename(self.subassets_group, self.assembly_top_node)
        logging.info('Topnode "{}" has been renamed "{}".'.format(self.subassets_group, self.assembly_top_node))
        # Create modeling note on topnode
        self.create_modeling_note()
        update_nodes.add_custom_attr(self.assembly_top_node, 'modeling_note', str(self.modeling_note))
        # Clean negatives transforms of -1 groups and freeze children meshes
        self.clean_negatives_transforms()
        # Freeze transform and delete history
        self.freeze_and_clean()
        # Delete namespace
        update_references.remove_namespaces()
        # Delete selection set
        self.clean_sets()
        # Delete unauthorized nodes due to ref flatting and clashing nodes
        sanity_check.SanityCheck()._fix_unauthorized()
        logging.info('Unauthorized nodes have been deleted.')
