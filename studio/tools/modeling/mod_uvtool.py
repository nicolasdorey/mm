# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#   AUTHOR :            Theodoric 'Kaerhene' JUILLET
#
#   DATE :              19/05/2020 - 17:54
#
#   DESCRIPTION :       Export UVs with preset values.
#
#   PRECAUTION :        None atm.
#
#   Update  1.0.0 :     We start here.
#   Update  1.1.1 :     Fix export problem with namespaces for Single mode.
#
#   KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

import os

try:
    import maya.cmds as cmds
except ImportError:
    pass

UV_SET_SUFFIX = '*_UvSet'


# ------------- #
# ---- UI ----- #
# ------------- #

def uv_tool_createui():
    # Prevent duplication
    window_tag = 'UV_Tool'
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag)

    # Version
    version = ' {}'.format('1.1.1')
    # Preroll
    default_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    # Main Window
    my_window = cmds.window(window_tag, title='UV Tool' + version, s=True, rtf=True)
    main_layout = cmds.rowColumnLayout(nc=1, cw=[1, 200])

    # UV Tools Bloc
    suffix_name = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 100), (3, 50)], p=main_layout)
    cmds.separator(height=15, style='in', p=suffix_name)
    cmds.text(label='UV Tools', align='center', p=suffix_name)
    cmds.separator(height=15, style='in', p=suffix_name)

    # UV Tools A Buttons
    uv_tool_a = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.optionMenu('selected_resolution', label='Select resolution :')
    menu_item_resolutions = [256, 512, 1024, 2048, 4096]
    for menu_item_resolution in menu_item_resolutions:
        cmds.menuItem(label=menu_item_resolution)
    cmds.optionMenu('selected_extension', label='Select extension :')
    menu_item_extensions = ['png', 'jpg']
    for menu_item_extension in menu_item_extensions:
        cmds.menuItem(label=menu_item_extension)
    cmds.optionMenu('selected_color', label='Select color :')
    menu_item_colors = ['Green', 'Red', 'Blue']
    for menu_item_color in menu_item_colors:
        cmds.menuItem(label=menu_item_color)

    uv_tool_b = cmds.rowColumnLayout(nc=3, p=main_layout)
    cmds.text(label='Mode : ', w=42, align='left')
    uv_tool_radiobutton_a = cmds.radioButtonGrp(
        'axis_radio_collection_a_name',
        labelArray3=['Single', 'Merged', 'Set'],
        nrb=3,
        sl=1,
        cw3=[52, 62, 60],
        en3=False)

    uv_tool_c = cmds.rowColumnLayout(nc=2, cw=[(1, 150), (2, 50)], p=main_layout)
    cmds.textField('textfield_a_name', tx=default_path, p=uv_tool_c)
    cmds.button(label='Browse...', h=20, c=update_browse_path, p=uv_tool_c)

    # Button Separator
    button_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=9, style='in', p=button_separator)
    cmds.button(label='Export UV',
                w=100,
                h=20,
                c=uv_export,
                p=button_separator)

    # Version Separator
    version_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=9, style='in', p=version_separator)

    # Version Display
    version_name = cmds.rowColumnLayout(nc=3, cw=[(1, 80), (2, 118)], p=main_layout)
    cmds.text(label='@Kaerhene', align='left', p=version_name)
    cmds.text(label='Version' + version, align='right', p=version_name)

    # Display the window
    cmds.showWindow(window_tag)


# ------------- #
# --- TOOLS --- #
# ------------- #

def uv_export(*args):
    uv_size = int(
        cmds.optionMenu('selected_resolution', query=True, value=True))
    uv_color = cmds.optionMenu('selected_color', query=True, value=True)
    uv_extension = cmds.optionMenu('selected_extension',
                                   query=True,
                                   value=True)
    uv_tool_radiobutton_a = cmds.radioButtonGrp(
        'axis_radio_collection_a_name', query=True, sl=True,
        la2=True)  # 1 for Single, 2 for Merged, 3 for UV
    uv_path = cmds.textField('textfield_a_name', query=True, tx=True)

    # Security check for last slash
    if uv_path[-1] != '\\':
        uv_path = '{}\\'.format(uv_path)

    # Setup color
    if uv_color == 'Green':
        uv_color = [0, 255, 0]
    elif uv_color == 'Red':
        uv_color = [255, 0, 0]
    elif uv_color == 'Blue':
        uv_color = [0, 0, 255]
    else:
        uv_color = [0, 255, 0]
        cmds.warning('--- Wrong color selected. Default (Green) will be used instead. ---')
    cmds.warning('--- Exporting, please wait... ---')

    uv_sets = cmds.ls(UV_SET_SUFFIX)
    mesh_list = cmds.ls(sl=True, r=True)
    sel_list = cmds.ls(sl=True, r=True)
    check_namespace = len(mesh_list[0].split(':')) > 1
    if check_namespace:
        padding = 0
        for mesh in mesh_list:
            new_name = mesh.split(":")[-1]
            mesh_list[padding] = new_name
            padding += 1

    # Exporting UVs
    if uv_tool_radiobutton_a == 1 and mesh_list:
        padding = 0
        for mesh_name in sel_list:
            cmds.select(mesh_name)
            if check_namespace:
                fixed_name = mesh_list[padding]
                export_uv(uv_extension, uv_size, uv_color, uv_path, fixed_name)
                padding += 1
            else:
                export_uv(uv_extension, uv_size, uv_color, uv_path, mesh_name)
    elif uv_tool_radiobutton_a == 2 and mesh_list:
        cmds.select(sel_list)
        export_uv(uv_extension, uv_size, uv_color, uv_path, "Merged")
    elif uv_tool_radiobutton_a == 3 and uv_sets:
        for uv_set in uv_sets:
            cmds.select(uv_set)
            export_uv(uv_extension, uv_size, uv_color, uv_path, uv_set)
    else:
        cmds.warning(
            '--- No mesh/UV Sets selected, please select and try again ! ---')
    cmds.select(sel_list)


def export_uv(uv_extension, uv_size, uv_color, uv_path, export_name):
    cmds.uvSnapshot(o=True,
                    ff=uv_extension,
                    xr=uv_size,
                    yr=uv_size,
                    aa=True,
                    r=uv_color[0],
                    g=uv_color[1],
                    b=uv_color[2],
                    n='{}{}.{}'.format(uv_path, export_name, uv_extension),
                    uMin=0,
                    uMax=1,
                    vMin=0,
                    vMax=1)
    cmds.warning('--- Export sucessfull ! Please check in {} ---'.format(uv_path))
    return uv_path


def update_browse_path(self):
    folder_path = cmds.fileDialog2(fileMode=3, caption="Choose export path")[0]
    cmds.textField('textfield_a_name', edit=True, tx=folder_path)


def open_window(self):
    folder_path = cmds.textField('textfield_a_name', query=True, tx=True)
    os.startfile(folder_path)


# Execute definition (DEBUG ONLY WITH SUBLIME)
# uv_tool_createui()
# openFolderBoxName = "openFolderBox"
# cmds.checkBox(openFolderBoxName, l="Open folder", al="right", p=ScreenButtonA, v=True)
# openFolderBoxQuery = cmds.checkBox(openFolderBoxName, query=True, value=True)
