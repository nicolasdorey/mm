# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##
#   AUTHOR :            Theodoric "KrNNN" JUILLET
#
#   DATE :              13/12/2019 - 13:50
#
#   DESCRIPTION :       Split scene in separated files from camera sequencer.
#
#   PRECAUTION :        None atm.
#
#   Update  1.0.0 :     We start here.
#           1.1.0 :     Now export cameras with the scene at the same location.
#                       Window can be opened even without sequencers in the scene.
#           1.2.0 :     Fix a problem when a shot have a namespace before his name.
#                       Locking cameras during export.
#                       Production purpose (Millimages Shotgun Pipeline) : Reverse suffix from node in maya with the Step name.
#           1.3.1 :     Now delete others shots in the splitted file.
#           1.3.2 :     Now will create folder if the one in the browse menu don't exist before.
#
#   KnownBugs :         None atm.
# -------------------------------------------------------------------------------------------------------------------------------------##
# -------------------------------------------------------------------------------------------------------------------------------------##

import os
import re

try:
    import maya.cmds as cmds
except ImportError:
    pass


# UI
def camseq_split_createui():
    # Prevent duplication
    window_tag = 'camseq_split'
    if cmds.window(window_tag, exists=True):
        cmds.deleteUI(window_tag)

    # Version
    version = ' {}'.format('1.3.2')
    # Preroll
    default_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    # Main Window
    my_window = cmds.window(window_tag, title='Camera Sequencer Splitter Tool' + version, s=True, rtf=True)
    main_layout = cmds.rowColumnLayout(nc=1, cw=[1, 200])

    # Camera Sequencer Splitter Bloc
    suffix_name = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 100), (3, 50)], p=main_layout)
    cmds.separator(height=15, style='in', p=suffix_name)
    cmds.text(label='Cam Seq Splitter', align='center', p=suffix_name)
    cmds.separator(height=15, style='in', p=suffix_name)

    # Camera Sequencer Splitter A Buttons
    camseq_split_a = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    get_sequencer_list()
    cmds.optionMenu('selected_sequencer', label='Select :')
    for sequencer in sequencer_list:
        cmds.menuItem(label=sequencer)

    camseq_split_b = cmds.rowColumnLayout(nc=2, cw=[(1, 148), (2, 60)], p=main_layout)
    cmds.text('Shots in sequencer :', align='left', p=camseq_split_b)
    cmds.text('{} shot(s)'.format(sequencer_len),
              align='left',
              p=camseq_split_b)

    camseq_split_c = cmds.rowColumnLayout(nc=3, p=main_layout)
    cmds.text(label='Mode : ', w=42, align='left', p=camseq_split_c)
    camseq_split_radiobutton_a = cmds.radioButtonGrp(
        'camseq_split_collection_a_name',
        labelArray2=['Same folder', 'Browse'],
        nrb=2,
        sl=1,
        cw2=[88, 62],
        p=camseq_split_c)

    camseq_split_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=3, style='double', p=camseq_split_separator)

    camseq_split_d = cmds.rowColumnLayout(nc=2, cw=[(1, 150), (2, 50)], p=main_layout)
    cmds.textField('textfield_a_name', tx=default_path, p=camseq_split_d)
    cmds.button(label='Browse...',
                h=20,
                c=update_browse_path,
                p=camseq_split_d)

    # Button Separator
    button_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=9, style='in', p=button_separator)

    # Split Button
    button_split = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.button(label='Start split', w=100, h=20, c=split_sequencer, p=button_split)

    # Version Separator
    version_separator = cmds.rowColumnLayout(nc=1, cw=[(1, 200)], p=main_layout)
    cmds.separator(height=9, style='in', p=version_separator)

    # Version Display
    version_name = cmds.rowColumnLayout(nc=3, cw=[(1, 80), (2, 118)], p=main_layout)
    cmds.text(label='@FollowKrNNN', align='left', p=version_name)
    cmds.text(label='Version' + version, align='right', p=version_name)

    # Display the window
    cmds.showWindow(window_tag)


# UV Tools def
def split_sequencer(self):
    FORCE_SAVE = True
    VERSION = 'v001'
    TASK_NAME = 'ANM'
    AXIS_LIST = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    REG_EXPRESSION = r'(.*)_(.*)_(.*).(v\d+.*?)$'

    camseq_split_radiobutton_a = cmds.radioButtonGrp(
        'camseq_split_collection_a_name', query=True, sl=True,
        la2=True)  # 1 for Browse, 2 for Same Folder
    user_path = cmds.textField('textfield_a_name', query=True, tx=True)
    # Security check for last slash
    if user_path[-1] != '\\':
        user_path = '{}\\'.format(user_path)
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    sequencer_to_split = cmds.optionMenu('selected_sequencer', query=True, value=True)
    if sequencer_to_split:
        original_file_path = cmds.file(q=True, loc=True)
        original_file_name = cmds.file(q=True, sn=True, shn=True)
        original_file_loc = original_file_path.replace(original_file_name, '')

        if camseq_split_radiobutton_a == 1:
            destination_file_path = original_file_loc
        elif camseq_split_radiobutton_a == 2:
            destination_file_path = user_path

        shots = cmds.listConnections(sequencer_to_split, type='shot')
        if shots:
            for shot in shots:
                # Get shot infos
                shot_name = cmds.getAttr('{}.shotName'.format(shot))
                if shot_name[0] == ':':
                    shot_name = shot_name.lstrip(':')
                shot_name_splitted = shot_name.split(':')[-1]
                shot_startframe = cmds.getAttr('{}.startFrame'.format(shot))
                shot_endframe = cmds.getAttr('{}.endFrame'.format(shot))

                # Setup scene with shot infos
                cmds.setAttr('defaultRenderGlobals.startFrame', shot_startframe)
                cmds.setAttr('defaultRenderGlobals.endFrame', shot_endframe)
                cmds.playbackOptions(min=shot_startframe, ast=shot_startframe, edit=True)
                cmds.playbackOptions(max=shot_endframe, aet=shot_endframe, edit=True)
                cmds.currentTime(shot_startframe, edit=True)

                # Split and cleanup
                camera_delete_list = cmds.ls('*_cam', r=True)
                shot_camera = cmds.listConnections(shot, t='camera')
                camera_delete_list.remove(shot_camera[0])

                shot_delete_list = cmds.ls('*_shot', r=True)
                shot_delete_list.remove(shot_name)

                try:
                    cmds.lookThru(shot_camera)
                except Exception as e:
                    print(e)
                    cmds.warning("--- Can't look through the camera, skipping... ---")
                export_name = '{}{}_{}.{}'.format(destination_file_path, shot_name_splitted, TASK_NAME, VERSION)

                # Regex rename to reverse step and extra_name from maya, should be in a def later
                regex = re.compile(REG_EXPRESSION, re.IGNORECASE)
                match = re.search(regex, export_name)
                if match:
                    name = match.group(1)
                    extra_name = match.group(2)
                    step = match.group(3)
                    version_extension = match.group(4)
                export_name = '{}_{}.{}'.format(name, step, version_extension)

                print('Now spliting : ', shot_name, shot_startframe,
                      shot_endframe)

                # Fbx export settings
                cmds.select(shot_camera)
                shot_camera_splitted = shot_camera[0].split(':')[-1]
                for axis in AXIS_LIST:
                    cmds.setAttr('{}.{}'.format(shot_camera[0], axis), lock=True)
                fbx_camera_name = ('{}{}_{}.{}.fbx'.format(destination_file_path, shot_camera_splitted, TASK_NAME, VERSION))

                # Regex rename to reverse step and extra_name from maya, should be in a def later
                regex = re.compile(REG_EXPRESSION, re.IGNORECASE)
                match = re.search(regex, fbx_camera_name)
                if match:
                    name = match.group(1)
                    extra_name = match.group(2)
                    step = match.group(3)
                    version_extension = match.group(4)
                fbx_camera_name = '{}_{}_{}.{}'.format(name, step, extra_name, version_extension)

                cmds.FBXResetExport()
                cmds.FBXExportUpAxis('z')
                cmds.FBXExportConvertUnitString('cm')
                cmds.FBXExportInAscii('-v', True)
                cmds.FBXExportCameras('-v', True)
                cmds.FBXExport('-f', fbx_camera_name, '-s')

                cmds.delete(camera_delete_list)
                cmds.delete(shot_delete_list)

                cmds.file(rename='{}.ma'.format(export_name))
                cmds.file(save=True, type='mayaAscii', f=FORCE_SAVE)
                cmds.file(original_file_path, open=True, f=True)

            cmds.file(original_file_path, open=True, f=True)
            cmds.warning('--- Succesfully splitted "{}" shots from "{}" ! Scene has been re-opened from original state... ---'.format(len(shots), sequencer_to_split))


def update_browse_path(self):
    folder_path = cmds.fileDialog2(fileMode=3, caption="Choose export path")[0]
    cmds.textField('textfield_a_name', edit=True, tx=folder_path)


def get_sequencer_list():
    global sequencer_list
    global sequencer_len
    sequencer_list = cmds.ls(typ='sequencer')
    if sequencer_list:
        shots_in_sequencer = cmds.listConnections(sequencer_list, type='shot')
        sequencer_len = len(shots_in_sequencer)
    else:
        sequencer_len = 0


# todo: def regex():
# todo: Add regex in def, remove from raw in script


# Dev def
def exe_wip(self):
    print('exeWIP'),

# Execute definition (DEBUG ONLY WITH SUBLIME)
# camseq_split_createui()
