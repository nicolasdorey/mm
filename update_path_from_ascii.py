import os
import re
import logging
import json
from datetime import datetime



# Path to change: path_to_walk_on
path_to_walk_on = os.path.normpath(r"\\srv-data1\Roaming_profile$\n.dorey\Desktop\tests\update_server_path")


# Update maya ascii scene from path_to_walk_on
update_server_path_log = "{}\update_server_path_log.json".format(path_to_walk_on)
regex = r"(P:.*Pirata2\/|P:.*Pirata2\\)"
new_assets_path = "L:/Millimages/PirataEtCapitano/PirataEtCapitano02/ProjectFiles"
obsolete_list = ["SCALE3", "Roaming_profile", "C:", "D:", "E:"]
# In case of crash, put already treated asset folders name in exception_directory
exception_directory = ["reference"]
maya_extension = ".ma"
# Get list of maya file in path_to_walk_on directory
maya_files_list = [os.path.join(root, x) for root, dirs, files in os.walk(path_to_walk_on) for x in files if x.endswith(maya_extension)]
data_list_logs = []
# Time log
current_time = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
time_log = "UPDATE DATE: {}".format(current_time)
logging.info(time_log)
data_list_logs.append(time_log)
# Edit ascii from each scene not in exception_directory
for maya_file_found in maya_files_list:
    for except_dir in exception_directory:
        if except_dir not in maya_file_found:
            data = 'Working on "{}"'.format(maya_file_found)
            data_list_logs.append(data)
            logging.info(data)
            # Open and write maya ascii
            with open(maya_file_found, 'r') as input_file:
                content = input_file.read()
                content_new = re.sub(regex, new_assets_path, content)
                for obsolete_tag in obsolete_list:
                    if obsolete_tag in content:
                        data = 'Obsolete tag "{}" found in "{}"!'.format(obsolete_tag, maya_file_found)
                        data_list_logs.append(data)
                        logging.error(data)
            with open(maya_file_found, 'w') as output_file:
                output_file.write(content_new)

# Save logs in a json file
with open(update_server_path_log, 'a') as f:
    json.dump(data_list_logs, f, indent=4)
