# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Julian Mayeux
#
#   DESCRIPTION :       ?
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import os
from PySide2 import QtCore, QtGui, QtWidgets

try:
    import sgtk
    import maya.cmds as cmds
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
    from maya import OpenMayaUI as omui
except ImportError:
    pass

from . import get_pictures_folders_from_asset as get_picture

EXT_OK = [".bmp", ".tiff", ".jpg", ".jpeg", ".png", ".tga"]


class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    def __init__(self, dir_path):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Reference Images")
        self.widget = QtWidgets.QVBoxLayout()
        self.main_widget = QtWidgets.QWidget()
        self.dir_path = dir_path

        self.all_tabs = QtWidgets.QTabWidget()
        self.widget.addWidget(self.all_tabs)
        self.main_widget.setLayout(self.widget)
        self.setCentralWidget(self.main_widget)

        self.statusBar()
        self.menu = self.menuBar()

        self.open_file = QtWidgets.QAction("&Open", self)
        self.clean_file = QtWidgets.QAction("Clean Perso", self)
        self.reload_file = QtWidgets.QAction("&Reload", self)

        self.menu.addAction(self.open_file)
        self.menu.addAction(self.clean_file)
        self.menu.addAction(self.reload_file)

        self.open_file.triggered.connect(self.file_open)
        self.clean_file.triggered.connect(self.clean_perso)
        self.reload_file.triggered.connect(self.file_reload)

        self.create_tab()

    def clean_perso(self):
        self.tab_perso.clean()

    def create_perso(self):
        self.tab_perso = TabWidget(name="Perso")
        self.all_tabs.addTab(self.tab_perso, self.tab_perso.name)

    def create_tab(self):
        self.create_perso()
        for path in self.dir_path:
            if os.path.exists(path):
                tab = TabWidget(path)
                self.all_tabs.addTab(tab, tab.name)

    def file_open(self):
        img_path = self.get_filename()
        self.tab_perso.add_img(img_path)

    def get_filename(self):
        path_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File')
        return path_name[0]

    def file_reload(self):
        for i in range(1, self.all_tabs.count()):
            tab = self.all_tabs.widget(i)
            tab.reload(self.dir_path[i-1])


class TabWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, path='', name=None):
        super(TabWidget, self).__init__()
        self.im_view = ImageView()
        if name:
            self.name = name
            self.init_perso()
        else :
            self.name = os.path.split(path)[1]
        layout = self.im_view.create_img(path)
        self.setLayout(layout)

    def init_perso(self):
        self.img_perso = []

    def add_img(self, path):
        self.im_view.add_img_ui(path)
        self.img_perso.append(path)

    def clean(self):
        self.im_view.clean_ui()

    def reload(self, dir_path):
        old = self.im_view.img_load
        self.clean()
        self.im_view.create_img(dir_path)
        new = self.im_view.img_load
        self.file_update_view(old, new)

    def file_update_view(self, img_before, img_after):
        message_text = " ====== MODIFICATIONS ======  /n/n"

        img_delete = []
        img_add = []
        for img in img_before:
            if img not in img_after:
                name = os.path.splitext(os.path.basename(img))[0]
                img_delete.append(name)
        for img in img_after:
            if img not in img_before:
                name = os.path.splitext(os.path.basename(img))[0]
                img_add.append(name)

        message_text = message_text + "ADDED : /n"
        if img_add:
            for name in img_add:
                message_text = message_text + name + "/n"
        else :
            message_text = message_text + "Nothing/n/n"

        message_text = message_text + "/nDELETED :/n"
        if img_delete:
            for name in img_delete:
                message_text = message_text + name + "/n"
        else :
            message_text = message_text + "Nothing/n"

        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle(self.name)
        message_box.setText(message_text)
        message_box.exec_()


class ImageView(QtWidgets.QWidget):
    def __init__(self):
        super(ImageView, self).__init__()
        self.layout_item = QtWidgets.QVBoxLayout()
        self.layout_item.setContentsMargins(10,10,10,10)
        self.ui_image_viewer = QtWidgets.QListView()
        self.layout_item.addWidget(self.ui_image_viewer)
        self.image_historique = []

        self.sld_size = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sld_size.setRange(100, 4000)
        self.sld_size.setValue(100)
        self.sld_size.valueChanged.connect(self.change_size)
        self.layout_item.addWidget(self.sld_size)

        self.ui_image_viewer.setViewMode(QtWidgets.QListView.IconMode)
        self.ui_image_viewer.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui_image_viewer.setIconSize(QtCore.QSize(100,100))
        self.ui_image_viewer.setMovement(QtWidgets.QListView.Free)
        self.ui_image_viewer.setModel(QtGui.QStandardItemModel())
        self.ui_image_viewer.clicked.connect(self.create_index)

        self.add_ui_imgplane()

    def abort(self):
        self.thread.quit()

    def add_ui_imgplane(self):
        self.down_layout = QtWidgets.QGridLayout()
        self.btn_create_plane = QtWidgets.QPushButton("Create image plane")
        self.btn_replace_plane = QtWidgets.QPushButton("Replace image plane")
        self.lbl_img_plane = QtWidgets.QLabel("Which image do you want replace :")
        self.lst_img_plane = QtWidgets.QComboBox()
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_done = QtWidgets.QPushButton("Ok")

        self.down_layout.addWidget(self.btn_create_plane, 0, 1, 1, 1)
        self.down_layout.addWidget(self.btn_replace_plane, 0, 2, 1, 1)
        self.down_layout.addWidget(self.lbl_img_plane, 1, 0, 1, 1)
        self.down_layout.addWidget(self.lst_img_plane, 1, 1, 1, 2)
        self.down_layout.addWidget(self.btn_cancel, 2, 1, 1, 1)
        self.down_layout.addWidget(self.btn_done, 2, 2, 1, 1)
        self.layout_item.addLayout(self.down_layout)

        self.btn_create_plane.clicked.connect(self.create_img_plane)
        self.btn_replace_plane.clicked.connect(self.visible_replace)
        self.btn_cancel.clicked.connect(self.hide_replace)
        self.btn_done.clicked.connect(self.replace_img_plane)

        self.btn_create_plane.setVisible(False)
        self.btn_replace_plane.setVisible(False)
        self.lbl_img_plane.setVisible(False)
        self.lst_img_plane.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_done.setVisible(False)

    def add_img_ui(self, path):
        item = self.img_to_icon(path)
        self.ui_image_viewer.model().appendRow(item)

    def change_size(self, value):
        self.ui_image_viewer.setIconSize(QtCore.QSize(value, value))

    def clean_ui(self):
        self.ui_image_viewer.model().clear()

    def create_img(self, dir_path):
        self.image_historique = []
        if dir_path:
            self.lst_image_path(dir_path)
            self.start_progress()
            self.thread.quit()
        return self.layout_item

    def create_index(self, index):
        self.index = index
        self.btn_create_plane.setVisible(True)
        all_img_plane = [name for name in cmds.ls(type="imagePlane")]
        if all_img_plane:
            self.btn_replace_plane.setVisible(True)
        else:
            self.btn_replace_plane.setVisible(False)
        self.update_lst_img_plane()

    def create_img_plane(self):
        image = self.image_historique[self.index.row()]
        cmds.imagePlane(fileName=image.path, name=image.name)
        cmds.rename(image.name)
        self.replace_img_plane(image.name)
        self.update_lst_img_plane()

        message_text = "====== CREATION ======\n\n"
        self.notif_img_plane(message_text, image)

    def hide_replace(self):
        self.lbl_img_plane.setVisible(False)
        self.lst_img_plane.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_done.setVisible(False)

    def img_to_icon(self, path):
        image = CustomImage(path)
        self.image_historique.append(image)
        return image.item

    def load_img(self):
        for path in self.img_load:
            self.add_img_ui(path)
            if len(self.img_load) > 1:
                self.prg_dialog.setValue(self.prg_dialog.value() + 1)

    def notif_img_plane(self, message_text, image):
        message_text = message_text + "Image plane : " + image.name
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle("IMAGE PLANE")
        message_box.setText(message_text)
        message_box.exec_()

    def replace_img_plane(self, name=None):
        if name: current_selection = name
        else: current_selection = self.lst_img_plane.currentText()
        image = self.image_historique[self.index.row()]
        cmds.select(current_selection, replace = True)
        cmds.imagePlane(current_selection, e=True, fileName=image.path, name=image.name)
        cmds.rename(image.name)
        self.update_lst_img_plane()

        if not name:
            message_text = "====== MODIFICATION ======\n\n"
            self.notif_img_plane(message_text, image)

    def lst_image_path(self, dir_path):
        self.img_load = []
        for f in os.listdir(dir_path):
            f_ext = os.path.splitext(f)[1]
            if f_ext in EXT_OK:
                self.img_load.append(os.path.join(dir_path, f))

    def start_progress(self):

        self.thread = QtCore.QThread(self)
        self.thread.started.connect(self.load_img)
        self.thread.start()

        nb_fichier = len(self.img_load)
        if nb_fichier > 1:
            self.prg_dialog = QtWidgets.QProgressDialog("Importing image...", "Cancel", 1, nb_fichier)
            self.prg_dialog.canceled.connect(self.abort)
            self.prg_dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.prg_dialog.show()

    def update_lst_img_plane(self):
        all_img_plane = [name for name in cmds.ls(type="imagePlane")]
        self.lst_img_plane.clear()
        self.lst_img_plane.addItems(all_img_plane)

    def visible_replace(self):
        self.update_lst_img_plane()
        self.lbl_img_plane.setVisible(True)
        self.lst_img_plane.setVisible(True)
        self.btn_cancel.setVisible(True)
        self.btn_done.setVisible(True)


class CustomImage(object):
    def __init__(self, path):
        self.path = path
        self.name = str(os.path.splitext(os.path.basename(path))[0])
        self.pixmap = QtGui.QPixmap(self.path)
        self.item = QtGui.QStandardItem(QtGui.QIcon(self.pixmap), self.name)


class Gallery(object):
    def run(self, restore=False):
        dir_path = self.get_dir_path()   
        print(dir_path)     
        customMixinWindow = MainWindow(dir_path)
        if customMixinWindow is None:
            customMixinWindow.setObjectName('GALLERY_UI')

        if restore == True:
            mixinPtr = omui.MQtUtil.findControl(customMixinWindow.objectName())
            # FIXME: restoredControl undefined!
            omui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(restoredControl))
        else:
            customMixinWindow.show(dockable=True, height=600, width=480, uiScript='run(restore=True)')

        customMixinWindow.resize(800, 800)
        customMixinWindow.show(dockable=True)

    def get_dir_path(self):
        current_engine = sgtk.platform.current_engine()
        # tk = current_engine.sgtk
        sg = current_engine.shotgun
        current_context = sgtk.platform.current_engine().context
        try:
            asset_id = current_context.entity['id']
            project_id = current_context.project["id"]
            dir_path = get_picture.find_folders(sg, project_id, asset_id, EXT_OK)
            return dir_path
        except:
            self.notif_erreur()
            return

    def notif_erreur(self):
        message_text = "You need to open an asset"
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle("ERROR")
        message_box.setText(message_text)
        message_box.exec_()


# ex = Gallery()
# ex.run()