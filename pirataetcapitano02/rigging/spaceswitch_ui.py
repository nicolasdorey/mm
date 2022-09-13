# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Sophie Chauvet
#
#   DESCRIPTION :       ?
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

import sys

try:
    import maya.cmds as cmds
    import pymel.core as pm
    from PySide2 import QtWidgets, QtCore
except ImportError:
    pass


class EditText(object):
    """
    This Class is used for adding QLineEdit item in the QListWidget
    """
    def __init__(self, content):
        self.le_driver_bls = QtWidgets.QLineEdit(content)

    def getText(self):
        return self.le_driver_bls.text()


class Spaceswitch_ui(object):
    def __init__(self):
        self.main_layout = QtWidgets.QGridLayout()
        # First line :
        # Create the line edit and the button Driven_ctrls, connect the button to the function
        self.driven_line_edit = QtWidgets.QLineEdit("")
        self.driven_ctrls_btn = QtWidgets.QPushButton("Driven_ctrls")
        self.driven_ctrls_btn.clicked.connect(self.drivenBT_action)
        # Add the widget to the grid layout (widget, line, column, height, width)
        self.main_layout.addWidget(self.driven_line_edit, 0, 0, 1, 3)
        self.main_layout.addWidget(self.driven_ctrls_btn, 0, 3, 1, 1)
        # Second line:
        # Create two listwidget for the drivers
        self.lw_driver_ctrls = QtWidgets.QListWidget()
        self.lw_bls = QtWidgets.QListWidget()
        self.main_layout.addWidget(self.lw_driver_ctrls, 1, 0, 2, 2)
        self.main_layout.addWidget(self.lw_bls, 1, 2, 2, 2)
        # Third and Fourth line :
        # Button "Driver_ctrls" for add drivers selected to the display and the runner
        self.btn_driver_ctrls = QtWidgets.QPushButton("Driver_ctrls")
        self.btn_driver_ctrls.clicked.connect(self.driverBT_action)
        self.btn_bls = QtWidgets.QPushButton("Launch Spaceswitch")
        self.btn_bls.clicked.connect(self.spaceswitchBT_action)
        self.main_layout.addWidget(self.btn_driver_ctrls, 3, 0, 1, 4)
        self.main_layout.addWidget(self.btn_bls, 4, 0, 1, 4)

    def drivenBT_action(self):
        """
        This function add the selection to the driven line edit
        """
        sel = cmds.ls(sl=True)
        self.driven_line_edit.setText(sel[0])

    def addItemsToList(self, items_to_add, liste, line_edit=False):
        """
        This function add the selection to the driven line edit
        :param items_to_add : the list off all items to add in the listwidget
        :type : list

        :param liste : listwidget in which one you want to add some items
        :type : QListWidget

        :param line_edit : by default is False, it is to have QLineEdit inside of the QListWidget
        :type : boolean

        :return : the liste of all items adding
        :rtype : list
        """
        if line_edit:
            all_lineEdit = []
            for add_item in items_to_add:
                # add a listWidgetItem and replace it by a QLineEdit
                item = QtWidgets.QListWidgetItem()
                liste.addItem(item)
                content_txt = add_item.name().replace(add_item.namespace(), '').split('_')[0]
                editText = EditText(content_txt)
                all_lineEdit.append(editText)
                liste.setItemWidget(item, editText.le_driver_bls)
            return all_lineEdit
        else:
            all_items = []
            for add_item in items_to_add:
                # add a listWidgetItem
                item = QtWidgets.QListWidgetItem(add_item)
                all_items.append(add_item)
                liste.addItem(item)
            return all_items

    def driverBT_action(self):
        """ Clean the two listWidget and add news items
        """
        self.lw_driver_ctrls.clear()
        self.lw_bls.clear()
        sel = cmds.ls(sl=True)
        self.all_driver_items = self.addItemsToList(sel, self.lw_driver_ctrls)
        pm_sel = pm.selected()
        self.all_bls_editText = self.addItemsToList(pm_sel, self.lw_bls, True)

    def spaceswitchBT_action(self, switch_attribute="space", use_rotate=False):
        driven_ctrls = self.driven_line_edit.text()
        drivers_ctrls = self.all_driver_items
        childs_space_nameGrpCL = self.all_bls_editText
        space_names = []
        if childs_space_nameGrpCL is not None:
            for child in childs_space_nameGrpCL:
                space_names.append(child.getText())
        drivers = []
        for i in range(0, len(drivers_ctrls)):
            drivers.append((drivers_ctrls[i], space_names[i]))
        print(drivers)
        # Create the space switch
        # FIXME: remove import from there!
        import cmt.rig.spaceswitch as spaceswitch
        spaceswitch.create_space_switch(
            driven_ctrls,
            drivers,
            switch_attribute=switch_attribute,
            use_rotate=use_rotate,
        )

    def launch(self):
        # Create the main widget and set the layout to show it
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)
        # window always on top
        self.main_widget.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.main_widget.setWindowTitle("SpaceSwitchWD")
        self.main_widget.resize(500, 500)
        self.main_widget.show()
        # without sys.exit() the display closes by itself
        sys.exit()
