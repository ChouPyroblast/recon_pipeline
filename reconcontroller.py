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
    parser.add_argument("--copytomdss", default="")
    parser.add_argument("--mdssproject", default="")
    parser.add_argument("--stage", default="")
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



elif os.system("ls tmp/*.json"):
    sys.exit(1)
else: # TODO accroding to the sys argument or existing file, to call different stage method
    pass


































"""



def mdssProjData():
    safeExec(
        "qsub -P $mango_proj -v MANGO_PROJECT=$mango_proj,MANGO_DIR=$mango_dir,MDSS_PROJECT=$mdss_proj, $mango_dir/mdss_projdata.sh")


def chooseReconPathway():
    doOnGPU = setDooOnGPU()
    if os.getenv("data_only") == "false":
        if doOnGPU == "true" or os.getenv("use_raijin_gpu") == "yes":
            if os.getenv("use_raijin_gpu") == "No":
                # if we are next on the GPU queue, proceed, else quit
                next_gpu_proj, next_gpu_sample = getNextGpuRun()
                if next_gpu_proj == os.getenv("project") and next_gpu_sample == os.getenv("sample"):
                    os.environ["stage"] = 'init_gpu_box_copy'
                else:
                    # add to gpu queue if not already in it.
                    if not os.system('grep -Fxq "${project}/${sample}" $HOME/.gpuReconQueue'):
                        print("job already found in GPU queue")
                    else:
                        os.system('"${project}/${sample}" >> $HOME/.gpuReconQueue')
                    sys.exit(1)
            else:
                os.environ["stage"] = 'init_reconstruct'
        else:
            os.environ["stage"] = "init_old_autofocus"
    else:
        sys.exit(1)


ef safeExec(cmd):
    if os.system(cmd):
        print("Error when try to run cmd:" + cmd)
        sys.exit(1)
    print(cmd)


def setDooOnGPU():

    return os.popen('cat /etc/services').read(
        "cat proju16_raw/expt*.in | grep -m1 \"iterative_trajectory\" | awk '{print $2}")


def getNextGpuRun():
    try:
        next = os.popen("head -n1 $HOME/.gpuReconQueue")
        next_gpu_prj = os.popen("`echo $next | cut -d/ -f1`")
        next_gpu_smp = os.popen("`echo $next | cut - d / -f2")
        print("Next GPU project/sample found to be {}/{}".format(next_gpu_prj, next_gpu_smp))
        return next_gpu_prj, next_gpu_smp
    except FileNotFoundError:
        sys.exit("Cannot find next gpu related files.")

def create_sbatch_file(sh_name,num_nodes,num_tasks,num_tasks_per_node,mango_proj,copy2mdss,mdss_proj,user,stage):
    shrun = "./sbatch_{}.sh".format(stage)
    with open(shrun,"w") as f:
        f.write("#!/usr/bin/env bash\n")
        f.write("#")
        if stage == "reconstruct_GPU":
            f.write("#SBATCH --ntasks-per-core=1 --nodes={} --ntasks={} --ntasks-per-node={} --gres=gpu:3 --time=24:00:00\n".format(num_nodes,num_tasks,num_tasks_per_node))
        else:
            f.write("#SBATCH --nodes=1 --ntasks=1 --time=24:00:00 --nodelist=master20\n")

        f.write("#\n")
        f.write("\n")
        f.write("export STAGE={}\n".format(stage))
        f.write("DATA_ONLY=false\n")
        f.write("export MANGO_DIR=/home/data20/appmaths/opt/bin\n")


currentstate = utils.RunState()

use_raijin_gpu = "no"
sample = currentstate.getSampleName()
project = currentstate.getProjectName()

# ?
if currentstate.isSLURM():
    if project == "y11":
        mdss_proj = "y11"
    elif not os.system("mdss -P h85 ls $project > /dev/null 2>&1"):
        mdss_proj = "h85"
    elif not os.system("mdss -P w09 ls $project > /dev/null 2>&1"):
        mdss_proj = "w09"
    else:
        if os.getenv("MDSS_PROJECT" == "h85"):
            mdss_proj = "h85"
        else:
            mdss_proj = "w09"
# Patch the slurm job id into the PBS one, in case we're on the cluster

pbs_jobid = os.getenv("SLURM_JOB_ID")

argvlen = len(sys.argv)
"""