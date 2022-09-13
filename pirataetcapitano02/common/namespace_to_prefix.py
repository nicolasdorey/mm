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

# TODO: do we really need sys?
import sys
import logging
from PySide2 import QtWidgets

try:
    from maya import cmds
except ImportError:
    pass

################################################### START UI ###################################################

class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        logging.info("MainWindow initialize...")
        self.DEFAULT_TRANSFORM = ['front', 'persp','top', 'side']
        self.DEFAULT_NS = ['UI','shared']
        self.setWindowTitle("PyNamespace")
        self.resize(960, 800)
        self.setup_ui()


    def setup_ui(self):
        self.create_widgets()
        self.create_layouts()
        self.modify_widgets()
        self.add_widgets_to_layouts()
        self.setup_connections()

    def create_widgets(self):
        self.lbl_namespace = QtWidgets.QLabel("Namespace : ")
        self.cb_namespace = QtWidgets.QComboBox()
        self.lbl_prefix = QtWidgets.QLabel("Prefix : ")
        self.le_prefix = QtWidgets.QLineEdit()
        self.lw_view = QtWidgets.QListWidget()
        self.lw_preview = QtWidgets.QListWidget()
        self.btn_preview = QtWidgets.QPushButton("Preview")
        self.btn_done = QtWidgets.QPushButton("Ok")


    def modify_widgets(self):
        self.cb_namespace.addItem(" - Select Namespace - ")
        self.cb_namespace.addItems(self.get_namespace())
        self.update_view()
        self.preview()

    def create_layouts(self):
        self.main_layout = QtWidgets.QGridLayout(self)

    def add_widgets_to_layouts(self):
        self.main_layout.addWidget(self.lbl_namespace, 0, 0, 1, 1)
        self.main_layout.addWidget(self.cb_namespace, 0, 1, 1, 2)
        self.main_layout.addWidget(self.lbl_prefix, 2, 0, 1, 1)
        self.main_layout.addWidget(self.le_prefix, 2, 1, 1, 2)
        self.main_layout.addWidget(self.lw_view, 3, 0, 1, 2)
        self.main_layout.addWidget(self.lw_preview, 3, 2, 1, 2)
        self.main_layout.addWidget(self.btn_preview, 7, 1, 1, 1)
        self.main_layout.addWidget(self.btn_done, 7, 2, 1, 1)

    def setup_connections(self):
        self.cb_namespace.currentIndexChanged.connect(self.update_view)
        self.btn_preview.clicked.connect(self.preview)
        self.btn_done.clicked.connect(self.change_namespace)


#################################################### END UI ####################################################


    def change_namespace(self):
        prefix_base = self.le_prefix.text()
        select_namespace = self.selection_namespace()
        sort_select_namespace = sorted(select_namespace, key=self.nb_childs, reverse=True)
        all_names = self.get_contains_name()

        for sort_name in sort_select_namespace:
            print (sort_select_namespace)
            i = 0
            for name in all_names :
                if sort_name in name :
                    try:
                        name = cmds.ls(name, sn=True)[0]
                    except:
                        name = name

                    base = sort_name + ":"
                    if prefix_base : prefix = prefix_base + "_"
                    else : prefix = prefix_base

                    rename = name.replace(base, prefix)
                    if "__" in rename :
                        rename = rename.replace("__", "_")

                    try:
                        cmds.lockNode(name, l=False)
                        cmds.rename(name, rename)
                    except:
                        logging.error('Can not rename name : %s', name)
                    all_names[i] = rename
                i+=1
            try :
                cmds.namespace(force= True, rm=sort_name, mergeNamespaceWithRoot=True)
            except :
                logging.error('Cannot rename namespace : %s', sort_name)

        self.cb_namespace.clear()
        self.cb_namespace.addItem(" - Select Namespace - ")
        self.cb_namespace.addItems(self.get_namespace())


    # Recupere les noms contenu dans la liste
    def get_contains_name(self) :
        select_namespaces = self.selection_namespace()
        all_names = [name for name in cmds.ls(l=True, r=True) if name not in self.DEFAULT_TRANSFORM]
        all_name_select = []
        all_names = sorted(all_names, key=self.nb_parents, reverse=True)

        for ns in select_namespaces :
            for name in all_names :
                if ns in name and name not in all_name_select :
                    name = cmds.ls(name, sn=True)[0]
                    all_name_select.append(name)
        return sorted(all_name_select, key=self.nb_parents, reverse=True)


    # Recupere les namespace et les enfants
    def get_namespace(self) :
        cmds.namespace(set=':')
        return [name for name in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) if name not in self.DEFAULT_NS]


    def update_view(self):
        all_names = self.get_contains_name()
        self.lw_view.clear()
        self.lw_view.addItems(all_names)
        self.preview()


    # Compte le nombre de ':' pour savoir le nombre d'enfants
    def nb_childs(self, ns):
        return ns.count(':')


    def nb_parents(self, name):
        return name.count('|')


    def preview(self):
        prefix = self.le_prefix.text()
        view_items = [self.lw_view.item(index).text() for index in range (self.lw_view.count())]
        select_namespace = self.selection_namespace()
        preview_items = []

        for ns in select_namespace:
            i = 0
            for item in view_items :
                if ns in item :
                    change = ns + ":"
                    print(change)
                    if prefix :
                        ajout = prefix + "_"
                    else :
                        ajout = ""
                    if '__' in ajout :
                        ajout = ajout.replace('__', '_')
                    rename = item.replace(change, ajout)
                    view_items[i] = rename
                    preview_items.append(rename)
                i += 1

        self.lw_preview.clear()
        self.lw_preview.addItems(preview_items)


    def selection_namespace(self):
        all_namespace = self.get_namespace()
        select_namespace = self.cb_namespace.currentText()
        lst_namespace = []
        for ns in all_namespace :
            if select_namespace in ns :
                lst_namespace.append(ns)
        return lst_namespace


    def launchUI(self):
        logging.info("Launch UI ...")
        self.show()
        sys.exit()

