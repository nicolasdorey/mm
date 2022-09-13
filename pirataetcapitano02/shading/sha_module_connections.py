# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       Connect shading modules to bridges textures.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import logging
import re

from ....studio.libs.reads import shaders as read_shaders
from ....studio.libs.updates import shaders as update_shaders
from ....studio.libs.deletes import shaders as delete_shaders

try:
    from PySide2 import QtWidgets
    import maya.cmds as cmds
    import sgtk
except ImportError:
    pass

import sha_module_connections_ui

ConnectShaModule_Ui = sha_module_connections_ui.ConnectShaModule_Ui

PROJECT_ID = 137
ASSET_LIB_SHA_ID = 1453
BUILD_NAME = "Build"
BRIDGE_TXT_NAME = "BridgeTexturing"
SHADING_STEP = "Shading"
TEXTURING_STEP = "Texturing"
SHA_MODULE_TASK = "ShaModule"


class ConnectShaModule(QtWidgets.QWidget, ConnectShaModule_Ui):
    def __init__(self, logger=logging):
        super(ConnectShaModule, self).__init__()
        self.setupUi(self)

        self.logger = logger
        current_engine = sgtk.platform.current_engine()
        current_context = sgtk.platform.current_engine().context
        self.sg = current_engine.shotgun

        # Import module from tk-framework-shotgun
        fw_shotgun = current_engine.apps.get('tk-multi-accessor').frameworks.get('tk-framework-shotgun')
        self.shotgun_read_steps = fw_shotgun.import_module('studio.libs.reads.steps')
        self.shotgun_read_tasks = fw_shotgun.import_module('studio.libs.reads.tasks')
        self.shotgun_read_published_files = fw_shotgun.import_module('studio.libs.reads.published_files')
        self.shotgun_read_asset_libraries = fw_shotgun.import_module('studio.libs.reads.asset_libraries')

        self.entity = current_context.entity
        self.asset_type = current_context.entity["type"]
        self.asset_name = current_context.entity["name"]
        self.task_name = current_context.task["name"]

        self.asset = self.asset_name.split('_')[0]
        self.variation_name = self.asset_name.split('_')[1]

        self.all_txt_entity = ""
        self.all_sha_entities = ""
        self.get_textures_files()

        self.connect_datas_to_ui()
        self.btn_validate.clicked.connect(self.validate_function)
        self.btn_update.clicked.connect(self.update_function)
        self.btn_shader_selected.clicked.connect(self.update_shader_nom)

        self.get_sha_modules()

    def get_textures_files(self):
        """
        Get all files of texturing that have been published
        """
        sg_step = self.shotgun_read_steps.get_step_by_name(self.sg, BUILD_NAME, self.asset_type)
        sg_task = self.shotgun_read_steps.get_task_by_name(self.sg, BRIDGE_TXT_NAME, sg_step, self.entity)
        task_id = sg_task["id"]
        self.all_txt_entity = self.shotgun_read_published_files.get_publish__with_checklatest(self.sg, task_id)
        # self.all_txt_entity =[{"code": "Canvas06_Classic_BLD_BridgeTexturing_Canvas_Dif_01.v003.u1002.png", "type": "PublishedFile", "id": 44127}, {"code": "Canvas06_Classic_BLD_BridgeTexturing_Canvas_Bmp_01.v003.u1002.png", "type": "PublishedFile", "id": 44333}, {"code": "Canvas06_Classic_BLD_BridgeTexturing_Frame_Dif_01.v003.u1001.png", "type": "PublishedFile", "id": 50069}]

    def get_sha_modules(self):
        """
        Get all the SHA modules available from the library
        """
        self.all_sha_entities = self.shotgun_read_asset_libraries.get_assets_from_assetslib(self.sg, ASSET_LIB_SHA_ID, PROJECT_ID)
        # self.all_sha_entities = [{"code": "SHADefault01_Character", "type": "Asset", "id": 4954, "task_template": {"type": "TaskTemplate", "id": 130, "name": "MM - Pirata2 - 3D SHA MODULES -"}}, {"code": "SHADefault01_Classic", "type": "Asset", "id": 4955, "task_template": {"type": "TaskTemplate", "id": 130, "name": "MM - Pirata2 - 3D SHA MODULES -"}}, {"code": "SHADefault01_Dull", "type": "Asset", "id": 4956, "task_template": {"type": "TaskTemplate", "id": 130, "name": "MM - Pirata2 - 3D SHA MODULES -"}}]

    def get_list_from_entity(self, entity):
        return [value["code"] for value in entity]

    def connect_txt_to_shader(self, texture_path, shader):
        """
        Connect path of texture to corresponding file node of module
        """
        files_of_shader = read_shaders.list_nodeType_of_shader(shader=shader, nodeType="file")
        if files_of_shader:
            for file in files_of_shader:
                type_of_file_node = self.get_texture_string_datas(texture=file, reg_pattern=r"File_[A-Z][a-z][a-z]")
                type_of_texture_path = self.get_texture_string_datas(texture=texture_path)
                if (
                    type_of_file_node
                    and type_of_texture_path
                    and type_of_file_node == type_of_texture_path
                ):
                    cmds.setAttr("{}.fileTextureName".format(file), texture_path, type="string")
                    cmds.setAttr("{}.colorSpace".format(file), "Raw", type="string")
                    self.logger.info('*' * 20 + "Texture {} \n has been plug into {} file Name and set to Raw".format(texture_path, file) + '*' * 20)

    def get_texture_string_datas(self, texture, reg_pattern=r'_[A-Z][a-z][a-z]_\d\d'):
        """
        Return texture type of file. ex: Dif
        """
        pattern = re.compile(reg_pattern)
        match = pattern.search(texture)
        if match:
            return match.group().split('_')[1]
        else:
            return None

    def get_publish_of_element(self, entity, step_name, task_name):
        """
        Get publish pathes of entity
        """
        step = self.shotgun_read_steps.get_step_by_name(self.sg, step_name=step_name, entity_type="Asset")
        # sg_task = self.shotgun_read_tasks.get_task_by_name(self.sg, "ShaModule", step, entity)
        sg_task = self.shotgun_read_tasks.get_task_by_name(self.sg, task_name, step, entity)

        publishes = self.shotgun_read_published_files.get_latest_publish_for_task(shotgun_api=self.sg, sg_entity=entity, sg_task=sg_task, published_file_type_name='Maya Scene')
        if publishes:
            return publishes["path"]["local_path_windows"]
        else:
            return None

    def import_element(self, publishes):
        """
        :param publishes: list of path published
        """
        result = []
        for publish in publishes:
            rnn = cmds.file(publish, i=True, rnn=True)
            result += rnn

        return result

    def update_tree_widget(self, widget, elements_list):
        """
        Update the tree widget with the list of elements given
        """
        if elements_list:
            for item in elements_list:
                widget.addItem(item)

    def connect_datas_to_ui(self):
        """
        Get datas and update UI with it
        """
        self.get_sha_modules()
        self.get_textures_files()
        modules_shaders = self.get_list_from_entity(entity=self.all_sha_entities)
        self.textures_list = self.get_list_from_entity(entity=self.all_txt_entity)
        self.update_function()
        self.update_tree_widget(widget=self.listWidgetModule, elements_list=modules_shaders)
        self.update_tree_widget(widget=self.listWidgetTextures, elements_list=self.textures_list)

    def get_fields(self, noCheck=False):
        """
        Get fields results of interface
        """
        self.module_selected = self.get_items_selected(widget=self.listWidgetModule)
        if self.module_selected:
            self.module_selected = self.module_selected[0].text()
        textures_selected = self.get_items_selected(widget=self.listWidgetTextures)
        if textures_selected:
            self.textures_selected = [item.text() for item in textures_selected]
        else:
            self.textures_selected = []
        self.shader_name = self.get_line_edit_text(lineEdit=self.le_shadername)
        self.extra_name = self.get_line_edit_text(lineEdit=self.le_extraname)
        if not noCheck and self.shader_name == "ShaderName":
            cmds.confirmDialog(m="Please give a shader name", title="Warning")
            return False

        all_existing_shaders = read_shaders.list_materials()
        if all_existing_shaders:
            for shader in all_existing_shaders:
                if '_' in shader:
                    if self.shader_name == shader.split('_')[2] and self.extra_name == shader.split('_')[3]:
                        cmds.confirmDialog(m="Shader name and extraname already used!!", title="Warning")
                        return False
                    else:
                        return True
        else:
            return True

    def get_all_publishes(self):
        """
        Get publishes for module and textures listed
        """
        module_entity = {}
        for module_available in self.all_sha_entities:
            if module_available["code"] == self.module_selected:
                module_entity = module_available

        textures_entities = []
        for texture_available in self.all_txt_entity:
            if texture_available["code"] in self.textures_selected:
                textures_entities.append(texture_available)

        self.module_publish = [self.get_publish_of_element(entity=module_entity, step_name=SHADING_STEP, task_name=SHA_MODULE_TASK)]

        self.textures_publishes = []
        # TODO : check from existing entity the import of the publish
        for texture_entity in textures_entities:
            publishedFileId = texture_entity["id"]
            texture_publish = self.shotgun_read_published_files.get_published_data(self.sg, publishedFileId, project_id=PROJECT_ID)
            if texture_publish is not None:
                self.textures_publishes.append(texture_publish["path"]["local_path_windows"])

    def validate_function(self):
        """
        Launch the import with renaming of elements
        """
        if not self.get_fields():
            return
        self.logger.info("modules items {}".format(self.module_selected))
        self.logger.info("textures items{}".format(self.textures_selected))
        self.logger.info("shader name {}".format(self.shader_name))
        self.logger.info("extra name {}".format(self.extra_name))

        # import module of shading
        self.get_all_publishes()
        shading_network_imported = self.import_element(publishes=self.module_publish)

        all_shaders = read_shaders.list_materials()
        imported_shaders = [shader for shader in all_shaders if shader is not None and shader in shading_network_imported]

        for shader in imported_shaders:
            if shader is not None:
                renamed_nodes = update_shaders.rename_shading_network(shader=shader, asset_name=self.asset, variation_name=self.variation_name, shader_name=self.shader_name, extra_name=self.extra_name, logger=self.logger)
                all_shaders = read_shaders.list_materials()
                shader = [shader for shader in all_shaders if shader is not None and shader in renamed_nodes]
                if shader:
                    shader = shader[0]
                    self.logger.info("****** published textures {}".format(self.textures_publishes))
                    for txt in self.textures_publishes:
                        self.connect_txt_to_shader(texture_path=txt, shader=shader)

                    self.logger.info("shader {}".format(shader))
                    if self.check_box:
                        empty_files = read_shaders.get_empty_files(shader)
                        all_files_of_shader = read_shaders.list_nodeType_of_shader(shader=shader, nodeType="file")
                        # keep all history of all nodes of files kept
                        kept_files = list(set(all_files_of_shader) - set(empty_files))
                        white_list = []
                        for file in kept_files:
                            down = cmds.listHistory(file, f=True)
                            for dow in down:
                                if dow == shader:
                                    break
                                else:
                                    white_list.append(dow)
                            up = cmds.listHistory(file, f=False)
                            for u in up:
                                if u == shader:
                                    break
                                else:
                                    white_list.append(u)

                        # self.logger.info("kept_files  {}".format(kept_files))
                        self.logger.info("empty files to remove {}".format(empty_files))
                        # self.logger.info("white list  {}".format(white_list))

                        for file in empty_files:
                            delete_shaders.clean_shading_network(shader=shader, node=file, white_list=white_list, logger=self.logger)

    def update_function(self):
        """
        Get extra name of tree widget item selected
        """
        self.get_fields(noCheck=True)
        if self.textures_selected:
            first_texture = self.textures_selected[0]
        else:
            if self.textures_list:
                first_texture = self.textures_list[0]
            else:
                first_texture = None
        if first_texture:
            tmp_extraname = self.get_texture_string_datas(texture=first_texture, reg_pattern=r"_(?:[A-Z][a-z]{1,}){1,}_[A-Z][a-z][a-z]_\d\d")
            self.le_extraname.setText(tmp_extraname)
        else:
            self.le_extraname.setText("Default")

        #     first_texture = self.textures_list[0]
        # tmp_extraname = self.get_texture_string_datas(texture=first_texture, reg_pattern=r"_(?:[A-Z][a-z]{1,}){1,}_[A-Z][a-z][a-z]_\d\d")
        # self.le_extraname.setText(tmp_extraname)

    def update_shader_nom(self):
        """
        Update nomenclature of shading network with context informations
        """
        if not self.get_fields():
            return
        shader = cmds.ls(sl=True)
        if len(shader) != 1:
            cmds.confirmDialog(m="Please Select a shader", title="Warning")
            return
        shader = shader[0]
        update_shaders.rename_shading_network(shader, self.asset, self.variation_name, self.shader_name, self.extra_name, logger=self.logger)

    def show_ui(self):
        self.form.show()


if __name__ == "__main__":
    ui = ConnectShaModule()
    ui.show_ui()
