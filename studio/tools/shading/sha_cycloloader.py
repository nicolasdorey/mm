# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Theodoric Juillet
#
#   DESCRIPTION :       Add and remove cyclo from the scene.
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import maya.cmds as cmds
except ImportError:
    pass


def import_cyclo():
    name = "Cyclo"
    padding = 1
    path = "L:/Millimages/Resources/turntables/Default/scenes/TurnMayaRedshift.ma"
    group_name = "{}_{:03d}_grp".format(name, padding)
    namespace = "{}_{:03d}".format(name, padding)
    existing_node = cmds.ls("{}_{:03d}RN".format(name, padding))
    if existing_node:
        cmds.file(rr=True, rfn="{}_{:03d}RN".format(name, padding))
        namespace_list = cmds.ls('Cyclo_*', long=True)
        for namespace in namespace_list:
            try:
                cmds.namespace(rm=namespace)
            except Exception as e:
                print(e)
                cmds.warning(
                    "--- Can't remove namespace '{}', skipping... ---".format(
                        namespace))
        cmds.warning("--- Cyclo deleted succesfully... ---")
    else:
        cmds.file(path,
                  r=True,
                  gr=True,
                  gn=group_name,
                  mnc=False,
                  ns=namespace)
        cmds.warning("--- Cyclo imported succesfully... ---")


if __name__ == "__main__":
    import_cyclo()
