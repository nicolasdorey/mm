# Copyright (c) 2020 Millimages
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

try:
    import sgtk
    from sgtk.platform.qt import QtGui, QtCore
except ImportError:
    pass


def get_editing_widget_for_template_key(key_name, key_value):
    """
    :param template_key:
    :return:
    """

    if isinstance(key_value, sgtk.IntegerKey):
        return IntegerFieldWidget(key_name, key_value)
    elif isinstance(key_value, sgtk.StringKey):
        if key_value.choices:
            return ComboBoxFieldWidget(key_name, key_value)
        else:
            return StringFieldWidget(key_name, key_value)


class IntegerFieldWidget(QtGui.QLineEdit):

    def __init__(self, key_name, key_value):
        """
        :param template_key:
        """
        super(IntegerFieldWidget, self).__init__()

        self._key_name = key_name
        self._key_value = key_value

        self.setValidator(QtGui.QIntValidator())

        if key_value.format_spec:
            self.setMaxLength(int(key_value.format_spec))

    def get_setting_value(self):
        """
        """
        value = self.text()
        if value != "":
            return int(value)
        return value

    def set_setting_value(self, setting_value):
        """
        """
        if not setting_value:
            self.setText("")
        else:
            self.setText(setting_value)


class StringFieldWidget(QtGui.QLineEdit):

    def __init__(self, key_name, key_value):
        """
        :param template_key:
        """
        super(StringFieldWidget, self).__init__()

        self._key_name = key_name
        self._key_value = key_value

        pattern = None

        if key_value.filter_by == "alpha":
            pattern = r"[\w\-]+"
        elif key_value.filter_by == "alphanumeric":
            pattern = r"[\w0-9\-]+"
        elif key_value.filter_by is not None:
            pattern = key_value.filter_by

        if pattern:
            self.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(pattern)))

    def get_setting_value(self):
        """
        """
        return self.text()

    def set_setting_value(self, setting_value):
        """
        """
        if not setting_value:
            self.setText("")
        else:
            self.setText(setting_value)


class ComboBoxFieldWidget(QtGui.QComboBox):

    def __init__(self, key_name, key_value):
        """
        :param template_key:
        """
        super(ComboBoxFieldWidget, self).__init__()

        self._key_name = key_name
        self._key_value = key_value

        choices_list = key_value.choices
        choices_list.sort()
        self.addItem("None")
        self.addItems(choices_list)

    def get_setting_value(self):
        """
        """
        return self.currentText()

    def set_setting_value(self, setting_value):
        """
        """
        self.setCurrentIndex(self.findText(setting_value))
