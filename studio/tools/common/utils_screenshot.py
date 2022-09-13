# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#  AUTHOR :            Theodoric "Kaerhene" JUILLET
#
#  DESCRIPTION :       Create a screenshot from the viewport into the project folder or a custom path.
#
#  Update  1.0.0 :     We start here.
#          1.1.0 :     Keep the current state of the camera.
#          1.2.0 :     Now can choose export path, default is same as 1.1.0.
#                      Now can save even if scene is not saved.
#
#  KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

import os
from datetime import datetime

try:
    import maya.cmds as cmds
except ImportError:
    pass

open_folder_box_name = "openFolderBox"
weight_name = "weightInt"
height_name = "heightInt"


# UI
def vp_screenshot_create_ui():
    # Prevent duplication
    window_tag = "exe_vp_screenshot"
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag)

    # Version
    version = "1.2.0"
    # Preroll
    FORCE_LOCAL = False
    if FORCE_LOCAL is True:
        default_path = "C:\\MayaScreenshots"
    elif FORCE_LOCAL is False:
        default_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

    # Main Window
    my_window = cmds.window(window_tag, title="exe_vp_screenshot {}".format(version), s=True, rtf=True)
    main_layout = cmds.rowColumnLayout(nc=1, cw=[1, 200])

    # Screen Tools Bloc
    screen_name = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 100), (3, 50)], p=main_layout)
    cmds.separator(height=15, style="in", p=screen_name)
    cmds.text(label="Screenshot Tool", align="center", p=screen_name)
    cmds.separator(height=15, style="in", p=screen_name)

    # Screen Tools Button
    screen_button_a = cmds.rowColumnLayout(nc=3, cw=[(1, 100), (2, 11)], p=main_layout)
    cmds.button(label="Take Screenshot", w=100, h=20, c=take_vp_screenshot, p=screen_button_a)
    cmds.text(l="", p=screen_button_a)  # Offset from cw2
    cmds.checkBox(open_folder_box_name, l="Open folder", al="right", p=screen_button_a, v=True)

    screen_button_b = cmds.rowColumnLayout(nc=3, cw=[(1, 65), (2, 67), (3, 67)], p=main_layout)
    cmds.text(label="Resolution : ", align="left")
    cmds.floatField(weight_name, p=screen_button_b, value=1920, pre=0)
    cmds.floatField(height_name, p=screen_button_b, value=1080, pre=0)

    screen_button_separator_a = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=3, style='double', p=screen_button_separator_a)

    screen_button_c = cmds.rowColumnLayout(nc=3, p=main_layout)
    cmds.text(label='Mode : ', w=42, align='left', p=screen_button_c)
    screen_button_radiobutton_a = cmds.radioButtonGrp(
        'screen_button_collection_a_name',
        labelArray2=['Project folder', 'Browse'],
        nrb=2,
        sl=1,
        cw2=[92, 62],
        p=screen_button_c)

    screen_button_separator_b = cmds.rowColumnLayout(nc=2, cw=[(1, 150), (2, 50)], p=main_layout)
    cmds.textField('textfield_a_name', tx=default_path, p=screen_button_separator_b)
    cmds.button(label='Browse...', h=20, c=update_browse_path, p=screen_button_separator_b)

    # Version Separator
    version_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=9, style="in", p=version_separator)

    # Version Display
    version_name = cmds.rowColumnLayout(nc=3, cw=[(1, 80), (2, 117)], p=main_layout)
    cmds.text(label="@Kaerhene", align="left", p=version_name)
    cmds.text(label="Version {}".format(version), align="right", p=version_name)

    # Display the window
    cmds.showWindow(window_tag)


def update_browse_path(self):
    folder_path = cmds.fileDialog2(fileMode=3, caption="Choose export path")[0]
    cmds.textField('textfield_a_name', edit=True, tx=folder_path)


def export_screenshot(camera_name, frame, images_location, raw_name,
                      weight_query, height_query, camera_display_res,
                      camera_display_gate_mask, camera_display_overscan):
    cmds.camera(camera_name, e=True, dr=False, dgm=False, ovr=1)  # Remove any Display option in the camera
    cmds.playblast(
        st=frame,
        et=frame,
        format="image",
        f="{}{}".format(images_location, raw_name),
        sqt=False,
        cc=1,
        v=False,
        orn=False,
        fp=4,
        percent=100,
        compression="png",
        quality=100,
        widthHeight=[weight_query, height_query],
        fo=True)
    cmds.camera(
        camera_name,
        e=True,
        dr=camera_display_res,
        dgm=camera_display_gate_mask,
        ovr=camera_display_overscan)  # Reset camera to the original state


def take_vp_screenshot(self, *args):
    # Retrieve workspace path and scene filename
    work_location = cmds.workspace(q=True, rd=True)
    images_location = "{}images/".format(work_location)
    filepath = cmds.file(q=True, sn=True)
    filename = os.path.basename(filepath)
    raw_name, extension = os.path.splitext(filename)
    # Retrieve values from the UI
    open_folder_box_query = cmds.checkBox(open_folder_box_name, query=True, value=True)
    weight_query = int(cmds.floatField(weight_name, query=True, value=True))
    height_query = int(cmds.floatField(height_name, query=True, value=True))
    # Retrieve path mode and value
    screen_button_radiobutton_a = cmds.radioButtonGrp(
        'screen_button_collection_a_name', query=True, sl=True,
        la2=True)  # 2 for Browse, 1 for Project Folder
    user_path = cmds.textField('textfield_a_name', query=True, tx=True)
    # Security check for last slash
    if user_path[-1] != '\\':
        user_path = '{}\\'.format(user_path)
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    if screen_button_radiobutton_a == 2:
        images_location = user_path

    # Retrieve actual frame number
    current_time_value = cmds.currentTime(q=True)
    frame = current_time_value

    # Verify if the targeted panel is a viewport
    actual_panel = cmds.getPanel(wf=True)
    is_model_panel = ("modelPanel" in actual_panel)
    if is_model_panel:
        camera_name = cmds.modelPanel(actual_panel, query=True, camera=True)
        # Get original Camera Display Options
        camera_display_res = cmds.getAttr("{}.displayResolution".format(camera_name))
        camera_display_gate_mask = cmds.getAttr("{}.displayGateMask".format(camera_name))
        camera_display_overscan = cmds.getAttr("{}.overscan".format(camera_name))

        if len(filename) == 0 and screen_button_radiobutton_a == 1:
            cmds.warning("--- File is not saved, aborting ! ---")
        else:
            if len(filename) == 0 and screen_button_radiobutton_a == 2:
                now = datetime.now()
                dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
                raw_name = dt_string
            export_screenshot(camera_name, frame, images_location, raw_name,
                              weight_query, height_query, camera_display_res,
                              camera_display_gate_mask,
                              camera_display_overscan)
            if open_folder_box_query is False:
                cmds.warning("--- Done ! Find your screenshot at {} ---".format(images_location))
            else:
                try:
                    os.startfile(images_location)
                except Exception as e:
                    print("Failed to open folder...")
                    print(e)
                cmds.warning("--- Done ! The folder will now open... If not, the pass is {} ---".format(images_location))
    else:
        cmds.warning("--- Please select a viewport and try again ! ---")


# Execute definition (DEBUG ONLY)
# vp_screenshot_create_ui()
