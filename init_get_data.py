import os
import reconcontroller
import json
import sys
import utils
from utils import save_json
"""
TODO: Maybe merge with recon.py
"""
cwd = os.getcwd()
sample = os.path.split(cwd)[1]
cwd = os.path.split(cwd)[0]
proj = os.path.split(cwd)[1]
cwd = os.path.split(cwd)[0]
workspace = os.path.split(cwd)[1]


def init_get_data():
    dic = utils.load_json(reconcontroller.json_dir ,reconcontroller.init_data_filename)
    acq_comp = None
    acqcom_user= None
    acqcom_root = None
    currentRoot = "g/data2/w09/CT_Data"



    home = os.getenv("HOME")
    f = open(os.path.join(home,".reconControllerComputerList"))

    s = f.readline()
    while s: # TODO check reconControllerComputerList
        s = f.readline()
        currentUser = ""  # TODO
        currentComputer = ""
        currentRoot = ""
        if currentUser != "#*":
            print("Looker for data in {}@{}:{}/{}/{}".format(currentUser,currentComputer,currentRoot,proj,sample))
            if not os.system("ssh $currentUser @$currentComputer test - d $currentRoot /$project /$sample"):
                acq_comp = currentComputer
                acqcom_root = currentRoot
                acqcom_user= currentComputer
    if acq_comp == None:
        print("couldn't find project/sample name")
        sys.exit("couldn't find project/sample name")

    dic["stage"] = "get_data"
    dic["acq_comp"] = acq_comp
    dic["acqcom_root"]   = acqcom_root
    dic["acqcom_user"] = acqcom_user
    save_json(dic)


    # cmd = "qsub -q copyq -N get_data -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=24:00:00,other=gdata4 -v STAGE=get_data,DATA_ONLY=$data_only,MANGO_DIR=$mango_dir,MANGO_EXE=$mango_exe,SH_NAME=$sh_name,MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=$copy2mdss,MDSS_PROJECT=$mdss_proj,SCRIPTNAME=$script,ACQCOMP=$acqcomp,ACQCOMPROOT=$acqcomp_root,ACQCOMPUSER=$acqcomp_user $script"
    cmd = "qsub -q copyq -N get_data -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=24:00:00,other=gdata4 get_data.py"  #TODO check the arguments of qsub
    if os.system(cmd):
        sys.exit("Cannot qsub {}".format())
    sys.exit(0)



def get_data():
    # cmd = "qsub -q copyq -N get_data -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=24:00:00,other=gdata4 -v STAGE=get_data,DATA_ONLY=$data_only,MANGO_DIR=$mango_dir,MANGO_EXE=$mango_exe,SH_NAME=$sh_name,MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=$copy2mdss,MDSS_PROJECT=$mdss_proj,SCRIPTNAME=$script,ACQCOMP=$acqcomp,ACQCOMPROOT=$acqcomp_root,ACQCOMPUSER=$acqcomp_user $script"
    cmd = "qsub -q copyq -N get_data -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=24:00:00,other=gdata4 get_data.py"  #TODO check the arguments of qsub
    if os.system(cmd):
        sys.exit("Cannot qsub {}".format())
    sys.exit(0)