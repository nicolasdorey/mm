# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Vicky Kirtsou
#                       Sophie Chauvet
#
#   DESCRIPTION :       Sgtk reads lib based on templates
#                       For shotgun requests you must use tk-framework-shotgun
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #

try:
    import sgtk
    from sgtk import TankError
except ImportError:
    pass

logger = sgtk.LogManager.get_logger(__name__)


def get_next_work_version_number(tk, context, work_template, work_fields=None):
    # WARNING: It's only for searching through work files
    # Get a list of existing file paths on disk that match the template and provided fields
    # Skip the version field as we want to find all versions not a specific version.
    file_paths = find_work_files(tk, context, work_template, work_fields=work_fields)
    versions = []
    for file_path in file_paths:
        # extract the values from the path so we can read the version.
        path_fields = work_template.get_fields(file_path)
        versions.append(path_fields["version"])

    # find the highest version in the list and add one.
    return max(versions) + 1 if versions else 1


def get_latest_work_file(tk, context, work_template, work_fields=None):
    file_paths = find_work_files(tk, context, work_template, work_fields=work_fields)
    # now loop over the files and find the highest version file
    latest_file = None
    highest_version = 0
    for a_file in file_paths:
        # extract the values from the path so we can read the version.
        path_fields = work_template.get_fields(a_file)
        if path_fields["version"] > highest_version:
            highest_version = path_fields["version"]
            latest_file = a_file
    return latest_file, highest_version


def get_latest_work_files(tk, context, work_template, work_fields=None):
    """
    returns: A dict of format:
        <extra_name> : {
            "highest_version": <int>,
            "latest_file": <path str>
        }
    """
    file_paths = find_work_files(tk, context, work_template, work_fields=work_fields, include_optional_fields=True)
    latest_files = {}
    for a_file in file_paths:
        # extract the values from the path so we can read the version.
        path_fields = work_template.get_fields(a_file)
        if "name" not in path_fields:
            path_fields["name"] = None
        print(path_fields)
        extra_name = path_fields["name"]

        if context.step["name"] == "Texturing" and "image_type" in path_fields:
            # For each extraName_textureType_padding in the filename, keep a separate record
            unique_key = "{}_{}_{}".format(path_fields["name"], path_fields["image_type"], path_fields["image_type_number"])
        else:
            # For each extra name in the filename, keep a separate record
            unique_key = path_fields["name"]

        if unique_key in latest_files:
            if path_fields["version"] > latest_files[unique_key]["highest_version"]:
                latest_files[unique_key]["highest_version"] = path_fields["version"]
                latest_files[unique_key]["latest_file"] = a_file
                latest_files[unique_key]["extra_name"] = path_fields["name"]
        else:
            latest_files[unique_key] = {
                "highest_version": path_fields["version"],
                "latest_file": a_file,
                "extra_name": path_fields["name"]
            }
    return latest_files


def find_work_files(tk, context, work_template, work_fields=None, skip_fields=[], include_optional_fields=False):
    # method _find_work_files() from workfiles2.file_finder
    """
    Find all work files for the specified context and work template.

    :param context:                         The context to find work files for
    :param work_template:                   The work template to match found files against
    :param ignore_fields:                   List of fields to ignore when comparing files in order to find
                                            different versions of the same file
    :returns:                               A list of file paths.
    """
    # find work files that match the current work template:
    if not work_fields:
        work_fields = []
        try:
            work_fields = context.as_template_fields(work_template, validate=True)
        except TankError as e:
            # could not resolve fields from this context. This typically happens
            # when the context object does not have any corresponding objects on
            # disk / in the path cache. In this case, we cannot continue with any
            # file system resolution, so just exit early insted.
            return []
    # Find all versions so skip the 'version' key if it's present and not
    # already registered in our wildcards:
    if not skip_fields:
        skip_fields = []
    if "version" not in skip_fields:
        skip_fields += ["version"]
    file_paths = tk.paths_from_template(
        work_template,
        work_fields,
        skip_fields,
        skip_missing_optional_keys=include_optional_fields
    )
    return file_paths
