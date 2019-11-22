#!/usr/bin/env python3
import os
import utils
import sys
import init_recon
dic = utils.load_json("stage.json")

"""
if project =="OCT:

"""


def mdssproj_data():
    cmd = "qsub -P $mango_proj -v MANGO_PROJECT={},MANGO_DIR={},MDSS_PROJECT={}, ${}/mdss_projdata.sh"\
        .format(dic["mango_proj"],dic["mango_proj"],dic["mango_dir"],dic["mdssproject"],dic["mango_dir"])
    utils.runCmd(cmd)


cmd = "python getfiles_pipelined.py --comp {} --user {} --root {} ".format(dic["acq_comp"],dic["acq_user"],dic["acq_root"])
result = os.system("cmd")
total_error = 0
while result == 1:
    total_error = total_error + 1
    if total_error >= 10:
        print("cannot transfer data")
        sys.exit(1)
    result = os.system("cmd")

if result == 0:
    print("Successfully transfer the data")

else:
    print("cannot transfer data")
    sys.exit(1)

if dic["copy2mdss"]:
    if dic["project"] == "OCT":
        pass #TODO mdss OCT
    else:
        mdssproj_data()
init_recon.recon()

#TODO write to stage.json