# TODO check launchReconProgram.sh
import os
import utils
import sys
import re
import argparse
import json
from init_get_data import init_get_data
from utils import save_json

stage_file = "stage" # TODO if we need random number here.
json_dir = "json"
##### functions

####
print("Welcome to reconController.sh")

# check if execute under recon_ws/project/sample
cwd = os.getcwd()
sample = os.path.split(cwd)[1]
cwd = os.path.split(cwd)[0]
proj = os.path.split(cwd)[1]
cwd = os.path.split(cwd)[0]
workspace = os.path.split(cwd)[1]

if workspace!="recon_ws":
    print("Fatal: Must be run from within recon_ws/project/sample.")
    sys.exit(1)

if "__ROI_0001" in sample or "__ROI_0002" in sample:
    print("Fatal: ROI data must be fetched from the main directory not the child scan.")
    sys.exit(1)

if os.getenv("PBS_JOBID"): # on cluster.   TODO find a better way to  check if iteractive.
    parser = argparse.ArgumentParser(description="input the .xml path and output file path")
    parser.add_argument("--project", default="", help="project (e.g. d59 or y11)")
    parser.add_argument("--bin_directory", default="")
    parser.add_argument("--executable", default="", help="without path, use bin_directory for path")
    parser.add_argument("--script", default="")
    parser.add_argument("--copytomdss", default=True)
    parser.add_argument("--mdssproject", default="")
    parser.add_argument("--stage", default="init_get_data")
    args = parser.parse_args()

    # $1 = project (e.g. d59 or y11)
    # $2 = bin_directory
    # $3 = executable (without path, use bin_directory for path)
    # $4 = script (without path, use bin_directory for path)
    # $5 = copy to mdss
    # $6 = mdss project (w09 or h85)
    # $7 = STAGE


    dic = {}
    dic["mango_proj"] = args.project
    dic["mango_dir"] = args.bin_directory
    dic["mango_exe"] = args.executable  ## ?
    dic["sh_name"] = args.script
    dic["copy2mdss"] = args.copytomdss
    dic["stage"] = args.stage
    dic["mdssproject"] = args.mdssproject
    save_json(dic)

    init_get_data(dic)



elif not os.path.exists("stage.json"):
    print("Cannot find stage.json file")
    sys.exit(1)


# TODO: 1. load json file if run on cluster.
#        2. start from other stage.











