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

# -*- coding: utf-8 -*-
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!
try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    pass

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class ConnectShaModule_Ui(object):
    def __init__(self):
        pass
    def setupUi(self, Form):
        self.form = Form
        self.form.setObjectName(_fromUtf8("Form"))
        self.form.resize(593, 432)

        self.gridLayoutWidget = QtWidgets.QWidget(self.form)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(-1, 16, 451, 401))
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))

        self.lb_title = QtWidgets.QLabel(self.gridLayoutWidget)
        self.lb_title.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_title.setObjectName(_fromUtf8("lb_title"))
        self.gridLayout.addWidget(self.lb_title, 0, 0, 1, 2)

        self.listWidgetTextures = QtWidgets.QListWidget(self.gridLayoutWidget)
        self.listWidgetTextures.setObjectName(_fromUtf8("listWidgetTextures"))
        self.listWidgetTextures.setSelectionMode((QtWidgets.QAbstractItemView.ExtendedSelection))

        self.listWidgetModule = QtWidgets.QListWidget(self.gridLayoutWidget)
        self.listWidgetModule.setObjectName(_fromUtf8("listWidgetModule"))

        self.gridLayout.addWidget(self.listWidgetTextures, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.listWidgetModule, 2, 0, 1, 1)

        self.btn_validate = QtWidgets.QPushButton(self.gridLayoutWidget)
        # self.btn_validate.setStyleSheet(_fromUtf8(qdarkstyle.load_stylesheet()))
        self.btn_validate.setObjectName(_fromUtf8("btn_validate"))
        self.gridLayout.addWidget(self.btn_validate, 3, 0, 1, 2)

        self.formLayoutWidget = QtWidgets.QWidget(Form)
        self.formLayoutWidget.setGeometry(QtCore.QRect(430, 70, 141, 91))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))

        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        # self.formLayout.setGeometry(QtCore.QRect(50, 150, 141*2, 91))
        self.formLayout.setSizeConstraint((QtWidgets.QLayout.SetFixedSize))

        # right elements
        self.lb_shaderName = QtWidgets.QLabel(self.formLayoutWidget)
        self.lb_shaderName.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_shaderName.setObjectName(_fromUtf8("lb_shaderName"))

        self.le_extraname = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.le_extraname.setObjectName(_fromUtf8("le_extraname"))

        self.lb_extraname = QtWidgets.QLabel(self.formLayoutWidget)
        self.lb_extraname.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_extraname.setObjectName(_fromUtf8("lb_extraname"))

        self.le_shadername = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.le_shadername.setObjectName(_fromUtf8("le_shadername"))

        self.btn_update = QtWidgets.QPushButton(self.formLayoutWidget)
        self.btn_update.setObjectName(_fromUtf8("btn_update"))

        self.btn_shader_selected = QtWidgets.QPushButton(self.formLayoutWidget)
        self.btn_shader_selected.setObjectName(_fromUtf8("btn_shader_selected"))

        self.label_vide = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_vide.setObjectName(_fromUtf8("label_vide"))

        self.formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.lb_shaderName)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.le_shadername)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.lb_extraname)
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.le_extraname)
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.btn_update)
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.SpanningRole, self.label_vide)
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.SpanningRole, self.label_vide)
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.label_vide)
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.btn_shader_selected)

        # QtCore.QMetaObject.connectSlotsByName(Form)

        Form.setWindowTitle(_translate("Form", "Connect Txt to Sha", None))
        self.lb_title.setText(_translate("Form", "Import of module and connections to textures", None))
        self.btn_validate.setText(_translate("Form", "Validate", None))
        self.lb_shaderName.setText(_translate("Form", "Shader Name", None))
        self.le_extraname.setText(_translate("Form", "ExtraName", None))
        self.lb_extraname.setText(_translate("Form", "Extra Name", None))
        self.le_shadername.setText(_translate("Form", "ShaderName", None))
        self.btn_update.setText(_translate("Form", "Get ExtraName", None))
        self.label_vide.setText('')
        self.btn_shader_selected.setText(_translate("Form", "Update Only Shader Selected", None))

    def get_items_selected(self, widget):
        return widget.selectedItems()

    def get_line_edit_text(self, lineEdit):
        return lineEdit.text()

# if __name__ == "__main__":
#     import sys
#     Form = QtWidgets.QWidget()
#     ui = ConnectShaModule_Ui()
#     ui(Form)
#     Form.show()
    # sys.exit(app.exec_())
