import os
import utils
import sys
import re


# TODO: change from os.system to subprocess.

##### functions

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


def safeExec(cmd):
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

# get the parameters
if pbs_jobid:
    script = os.getenv("SCRIPTNAME")
    mango_proj = os.getenv("MANGO_PROJECT")
    mango_dir = os.getenv("MANGO_DIR")
    mango_exe = os.getenv("MANGO_EXE")
    sh_name = os.getenv("SH_NAME")
    copy2mdss = os.getenv("COPY_TO_MDSS")
    mdss_proj = os.getenv("MDSS_PROJECT")
    stage = os.getenv("STAGE")
    data_only = os.getenv("DATA_ONLY")
else:
    if argvlen <= 5 and argvlen != 3:
        print("""
            Usage:"
              reconController.sh mango_dir stage"
              or"
              reconController.sh project mango_dir mango script copy_to_mdss"
              or"
              reconController.sh project mango_dir mango script copy_to_mdss stage"
              or"
              reconController.sh project mango_dir mango script copy_to_mdss mdss_project stage"
            
                 where: mango_dir and stage as above"
                        project      = d59 or y11"
                        mango_dir = path to mango executable to use"
                        mango        = mango executable without path, has to be in mango_dir"
                        script       = name of this .sh file without path, has to be in mango_dir"
                        copy_to_mdss = if true backup projection and reconstruction data to mdss"
                        mdss_project = w09, h85, or y11"
                        stage     = stage of process at which to start, options include:"
                                    init_get_data (default)"
                                    init_get_data_only"
                                    init_old_autofocus"
                                    init_reconstruct"
                                    init_copy"
                                    init_accept (for deleting all working directories of a finished recon)"
        """)
        sys.exit(1)
    if argvlen == 3:
        script = os.path.join(sys.argv[1], "reconController.sh")
        mango_proj = project
        mango_dir = sys.argv[1]
        mango_exe = "mango"
        sh_name = "reconController.sh"
        copy2mdss = True
        mdss_project = "AUTO_DETECT"
        stage = sys.argv[2]
        data_only = False
    else:
        script = os.path.join(sys.argv[2], sys.argv[4])
        mango_proj = sys.argv[1]
        mango_dir = sys.argv[2]
        mango_exe = sys.argv[3]
        sh_name = sys.argv[4]
        copy2mdss = sys.argv[5]
        if argvlen == 6:
            mdss_project = "AUTO_DETECT"
            stage = "init_get_data"
            data_only = False
        elif argvlen == 7:
            mdss_project = "AUTO_DETECT"
            stage = sys.argv[6]
            data_only = False
        elif argvlen == 8:
            mdss_proj = sys.argv[6]
            stage = sys.argv[7]
            data_only = False

        # set according to different stage.
        if stage == "init_get_data_only":
            data_only = True
            stage = "init_get_data"
        elif stage == "init_get_data_mdss_only":
            data_only = True
            stage = "init_get_data_mdss"
        else:
            data_only = False
    if mdss_project == "AUTO_DETECT":
        if project == "y11":
            mdss_proj = "y11"
        elif not os.system("mdss -P h85 ls $project > /dev/null 2>&1"):
            mdss_proj = "h85"
        elif not os.system("mdss -P w09 ls $project > /dev/null 2>&1"):
            mdss_proj = "w09"
        elif os.getenv("MDSS_PROJECT" == "h85"):
            mdss_proj = "h85"
        else:
            mdss_proj = "w09"

    print("""
    launching reconstruction with:
    project    = {}
    sample     = {}
    script     = {}
    mango_proj = {}
    mango_dir  = {}
    mango_exe  = {}
    copy2mdss  = {}
    mdss_proj  = {}
    stage      = {}
    data_only  = {}
    """.format(project, sample, script, mango_proj, mango_dir, mango_exe, copy2mdss, mdss_proj, stage, data_only))

###### if we have run out of quota on d59, use 209 temporarily by creating the file __D59_W09_override__ in $HOME

if mango_proj == "d59":
    if os.path.isfile("__D59_W09_override__"):
        mango_proj = "w09"

if stage == "init_get_data":
    # update status
    cmd = "qsub -P {} -v MANGO_RECON_STATUS={} -W umask=027 -lother=gdata2 {}/putReconInfo.sh"
    os.system(cmd)

    # Verify that the data directory is correct before queuing a job to
    # catch potential issues at launch time. Each potential acquisition computer needs to be specified here.
    # This allows for a different username, and different directory structure on each machine.

    currentroot = "/g/data2/w09/CT_Data"
    # TODO check this section of code.

    acqcomp = "not_found"

    if acqcomp == "not_found":
        print("cound not find project/sample name on g/data2")
        print("checking computer list in home/.reconControllerComputerList")
        with open("{}/.reconControllerComputerList".format(os.getenv("HOME"))) as f:
            for currentlocation in f.readlines():  # TODO: consider using regex instead
                currentlocation = currentlocation[:-1]

                currentcomputer = currentlocation[currentlocation.index("@"):currentlocation.index(":")]
                currentuser = currentlocation[:currentlocation.index("@")]
                currentroot = currentlocation[currentlocation.index(":") + 1:]

                # check availiable.

                if not currentuser.startswith("#"):  # TODO: check condition here later.
                    print(
                        "looking for data in {}@{}:{}/{}/{}".format(currentuser, currentcomputer, currentroot, project,
                                                                    sample))
                    if not os.system(
                            "ssh {}@{} test -d {}/{}".format(currentuser, currentcomputer, currentroot, project)):
                        if not os.system(
                                "ssh {}@{} test -d {}/{}/{}".format(currentuser, currentcomputer, currentroot, project,
                                                                    sample)):
                            print("Found {} on {}".format(sample, currentcomputer))
                            acqcomp = currentcomputer
                            acqcomp_root = currentroot
                            acqcomp_user = currentuser
                        else:
                            print("No such sample on {}@{} :{}/{}/{}".format(currentuser, currentcomputer, currentroot,
                                                                             project, sample))
                    else:
                        print("No such project on {}@{} :{}/{}".format(currentuser, currentcomputer, currentroot,
                                                                       project))

    if acqcomp == "not_found":
        print("cound not find project/sample name")
        sys.exit(1)

    os.system(
        "echo \"{} {} {} {} {} {} {} init_get_data\" > launchReconProgram.sh".format(script, mango_proj, mango_dir,
                                                                                     mango_exe, sh_name, copy2mdss,
                                                                                     mdss_proj))
    os.system("chmod u+x launchReconProgram.sh")
    cmd = "qsub -q copyq -N get_data -P {} -W umask=027 -lncpus=1,mem=2GB,walltime=24:00:00,other=gdata2 -v " \
          "STAGE=get_data,DATA_ONLY={},MANGO_DIR={},MANGO_EXE={},SH_NAME={}," \
          "MANGO_PROJECT={},COPY_TO_MDSS={}," \
          "MDSS_PROJECT={},SCRIPTNAME={},ACQCOMP={}," \
          "ACQCOMPROOT={},ACQCOMPUSER={} {}".format(mango_proj, data_only, mango_dir, mango_exe, sh_name, mango_proj,
                                                    copy2mdss, mdss_proj, script, acqcomp, acqcomp_root, acqcomp_user,
                                                    script)
    print(cmd)
    os.system(cmd)
    sys.exit(0)

if os.getenv(
        "stage") == "get_data":  # TODO: get-data: live, commencing ~5 minutes after acquisition commences. Checksums, reliable enough that we auto-delete from the acquisition machine after transfer.
    # update status:
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)

    print("Copying data from acquisition computer...")
    print("wd=$PWD")
    cmd = "$mango_dir/getExptData.sh $ACQCOMP $ACQCOMPUSER $ACQCOMPROOT"
    if os.system(cmd):
        sys.exit(1)
    print("Data copied successfully")

    # stash data on MDSS

    if os.getenv("copy2mdss") == "true":
        mdssProjData()
    chooseReconPathway()

if os.getenv("stage") == "init_get_data_mdss":
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)

    os.system(
        'echo "$script $mango_proj $mango_dir $mango_exe $sh_name $copy2mdss $mdss_proj init_get_data_mdss" > launchReconProgram.sh')
    os.system("chmod u + x launchReconProgram.sh")

    cmd = "qsub -q copyq -N get_data_mdss -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=10:00:00 -v STAGE=get_data_mdss,DATA_ONLY=$data_only,MANGO_DIR=$mango_dir,MANGO_EXE=$mango_exe,SH_NAME=$sh_name,MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=$copy2mdss,MDSS_PROJECT=$mdss_proj,SCRIPTNAME=$script $script"
    print(cmd)
    os.system(cmd)
    sys.exit(0)

if os.getenv("stage") == "get_data_mdss":
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)
    print("copy data from mdss")
    print("wd = " + os.path.curdir)
    safeExec("$mango_dir/getMdssData.sh")
    print("data copied successfully")
    chooseReconPathway()

if os.getenv("stage") == "init_old_autofocus":
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)

    print("copying autofocus files to current directory")

    os.system('cp "/short/d59/xct110/AfTemplates/autofocus.in" .')
    os.system('cp "/short/d59/xct110/AfTemplates/autofocus_run.sh" .')
    os.system('chmod +x ./autofocus_run.sh')
    cmd = "qsub -N old_autofocus -P $mango_proj -W umask=027 -lncpus=256,mem=1024GB,walltime=10:00:00 -v STAGE=old_autofocus,DATA_ONLY=false,MANGO_DIR=$mango_dir,MANGO_EXE=$mango_exe,SH_NAME=$sh_name,MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=$copy2mdss,MDSS_PROJECT=$mdss_proj,SCRIPTNAME=$script $script"
    print(cmd)
    os.system(cmd)
    sys.exit(0)
if os.getenv("stage") == "old_autofocus":
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)

    cmd = "./autofocus_run.sh"
    print(cmd)
    if os.system(cmd):
        sys.exit(1)
    print("Autofocus done successfully")
    os.environ["stage"] = "init_reconstruct"

if os.getenv("stage") == "init_gpu_box_copy":
    # The gpu_box_copy stage should copy the data to the GPU box, and then pass control there.
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)

    os.system(
        'echo "$script $mango_proj $mango_dir $mango_exe $sh_name $copy2mdss $mdss_proj init_gpu_box_copy" > launchReconProgram.sh')
    os.system("chmod u+x launchReconProgram.sh")

    safeExec(
        "qsub -q copyq -N gpu_box_push -P $mango_proj -W umask=027 -lncpus=1,mem=2GB,walltime=10:00:00 -v STAGE=gpu_box_copy,DATA_ONLY=false,MANGO_DIR=$mango_dir,MANGO_EXE=$mango_exe,SH_NAME=$sh_name,MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=true,MDSS_PROJECT=$mdss_proj,SCRIPTNAME=$script $script")

    sys.exit(0)

if os.getenv("stage") == "gpu_box_copy":
    print("copying  data to gpu box")
    gpu_location = "/home/appmaths/recon_ws/{}/{}".format(project, sample)
    gpu_user = "appmaths"
    gpu_machine = "am053.anu.edu.au"
    cmd = "ssh ${gpu_user}@${gpu_machine} 'mkdir -p ${gpu_location}/proju16_raw'".format(gpu_user, gpu_machine,
                                                                                         gpu_location)
    print(cmd)
    os.system(cmd)
    os.system("module load numpy")
    cmd = "${mango_dir}/pushReconData.py"
    if not os.system(cmd):
        sys.exit(1)
    print("Data copied successfully")

    os.environ["stage"] = "init_reconstruct"

if os.getenv("stage") == "init_reconstruct":
    cmd = "qsub -P $mango_proj -v MANGO_RECON_STATUS=$stage -W umask=027 -lother=gdata2 $mango_dir/putReconInfo.sh"
    os.system(cmd)
    num_projections = len(os.listdir("proju16_raw"))
    print("numProjs = " + str(num_projections))

    size_projections_bytes = int(os.popen("ls -l ./proju16_raw/*_CF000000.raw | awk '{print $5}'").read())
    size_projections_megaPixels = size_projections_bytes / (1024 * 1024 * 2)  # TODO: int or double?
    if size_projections_megaPixels == 0:
        size_projections_megaPixels = 1
    print("sizeProjs = {} megaPixels".format(size_projections_megaPixels))

    nprocs = 16 * size_projections_megaPixels * (1 + num_projections / 2048)
    trajectoryType = os.popen("cat proju16_raw/*_tomo.in | grep trajectory | awk '{print $2}'").read()

    if "irc" in trajectoryType:
        print("trajectory is circular")
        if nprocs > 192:
            nprocs = 192
        if size_projections_megaPixels > 4:
            walltime = "6:00:00"
        else:
            walltime = "2:00:00"
    else:
        print("trajectory is helical")
        if nprocs > 256:
            nprocs = 256
        if size_projections_megaPixels > 4:
            walltime = "36:00:00"
        else:
            walltime = "12:00:00"

    if size_projections_megaPixels > 4:
        print("Large FlatPanel detector, therefore assigning 4GB mem per node")
        mem = nprocs * 4
    else:
        mem = nprocs * 2

    print("nprocs = " + str(nprocs))
    print("mem = " + str(mem))
    print("walltime = " + walltime)

    os.system(
        'echo "$script $mango_proj $mango_dir $mango_exe $sh_name $copy2mdss $mdss_proj init_reconstruct" > launchReconProgram.sh')
    os.system('chmod u+x launchReconProgram.sh')

    doOnGpu = setDooOnGPU()
    if doOnGpu == "true" and os.getenv("use_raijin_gou") == "no":
        print("Doing space filling on GPU boxes")
        gpu_location = "/home/appmaths/recon_ws/{}/{}".format(project, sample)
        os.environ["gpu_location"] = gpu_location
        gpu_user = "appmaths"
        gpu_name = "am053.anu.edu.au"
        print("copy launchReconProgram.sh to gpu cluster")
        os.system("doRsync.sh ./launchReconProgram.sh {}@{}:{}".format(gpu_user, gpu_name, gpu_location))
        # Set up the environment variables for the GPU box
        gpu_env = "STAGE=reconstruct_GPU,DATA_ONLY=false,MANGO_DIR=/home/data20/appmaths/opt/bin," \
                  "MANGO_EXE=mango,SH_NAME=${sh_name},MANGO_PROJECT=$mango_proj,COPY_TO_MDSS=$copy2mdss," \
                  "MDSS_PROJECT=$mdss_proj,SCRIPTNAME=${gpu_location}/${sh_name}"

        print(os.environ["gpu_location"] + os.environ[sh_name])
        # The GPU submission

        num_nodes = 1
        num_tasks_per_node = 3
        num_tasks = 3

        #### recommended CPU layouts ###
        # if 3K (jpv Pixium is 2880x2881, I'll include it in this option: 2 nodes - 3 procs/node
        big_monitor = 2800 * 2800 * 2
        # if 2K:
        #    if < 5000 proj 1node - 3procs/node
        #    if > 5000 proj 2 node - 3procs/node
        medium_monitor = 2000 * 2000 * 2
        # if 1.5k 1 node - 3 procs
        if size_projections_bytes > big_monitor:
            num_nodes = 2
            num_tasks = 6
        else:
            if num_projections > 5000:
                num_nodes = 2
                num_tasks = 6

        print("Setting num_nodes to {} and num_tasks to {}".format(num_nodes, num_tasks))
