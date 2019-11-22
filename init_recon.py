import sys
import os
from shutil import copyfile
from utils import getOSCommand
from utils import runCmd
from utils import RunState
import datetime
import utils
import random
import parameters

dic = utils.load_json("stage.json")


def recon():
    if dic["data_only"]:
        sys.exit(0)

    # if dic["project"] == "DeBeers" or dic["project"] == "Testing_Mk2" :
    # TODO

    # queueOnGPU

    os.system('echo "`date`: pipeline handover to GPU" >> STATUS_RECON.txt')
    status_recon = utils.AtomicFile("STATUS_RECON.txt")
    status_recon.append(str(datetime.datetime.now()))
    status_recon.save(replace=True)

    reconSystem = "GPU"

    isAxialROI = RunState.isROI()
    isSFT = RunState.doOnGPU()
    isTall = RunState.isTall()

    reconType = "dH"

    if isAxialROI:
        reconType = "SFT_AxialROI"
        projDirs = ("proju16_roi_raw", "proju16_overview_raw")
    elif isSFT:
        reconType = "SFT"
    elif isTall:
        reconType = "dH_pcm"

    TEMPLATEDIR = os.path.join(dic['mango_dir'], 'templates')

    if not os.isfile("recon.template.in"):
        srcfilename = "{}/recon.{}_{}.template.in".format(TEMPLATEDIR, reconSystem, reconType)
        destname = "recon.template.in"
        copyfile(srcfilename, destname)

    if not os.isfile("recon.template.slurm.sh"):
        srcfilename = "{}/recon.{}_{}.template.slurm.sh".format(TEMPLATEDIR, reconSystem, reconType)
        destname = "recon.template.slurm.sh"
        copyfile(srcfilename, destname)

        projSizeGB = getOSCommand("du --apparent-size --block-size=1G -s ${projDirs[0]}/ | sed 's#\s.*$##'")
        memNeededGB = projSizeGB * 15
        MATCHQSPEC = '--partition=gpucluster0'
        QSPEC = MATCHQSPEC

        if isAxialROI:
            if memNeededGB < 500:
                QSPEC = '--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --nodes=1 --exclusive'
            elif memNeededGB < 1000:
                QSPEC = '--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --use-min-nodes --constraint=[gpu2A*1\&gpu2B*1] --exclusive'
            elif memNeededGB < 1500:
                QSPEC = '--partition=gpu8_15_A,gpu8_15_B,LOgpucluster0,LOgpu8_30_A --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
            elif memNeededGB < 2800:
                QSPEC = '--partition=gpu8_30_A,LOgpucluster0,gpu8_15_A,gpu8_15_B --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
            else:
                QSPEC = '--partition=LOgpu8_30_A,LOgpucluster0,gpu8_15_A,gpu8_15_B --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
        elif isSFT:
            if ((memNeededGB < 500)):
                QSPEC = '--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --nodes=1 --exclusive'
            elif ((memNeededGB < 1000)):
                QSPEC = '--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --use-min-nodes --constraint=[gpu2A*1\&gpu2B*1] --exclusive'
            elif ((memNeededGB < 1500)):
                QSPEC = '--partition=gpu8_15_A,gpu8_15_B,LOgpucluster0,LOgpu8_30_A --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
            elif ((memNeededGB < 2800)):
                QSPEC = '--partition=gpu8_30_A,LOgpucluster0,gpu8_15_A,gpu8_15_B --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
            else:
                QSPEC = '--partition=LOgpu8_30_A,LOgpucluster0,gpu8_15_A,gpu8_15_B --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
        else:
            if ((memNeededGB < 500)):
                QSPEC = '--partition=gpucluster0 --use-min-nodes --nodes=1 --exclusive'
            elif ((memNeededGB < 1000)):
                QSPEC = '--partition=gpucluster0 --use-min-nodes --nodes=2 --exclusive'
            else:
                QSPEC = '--partition=gpucluster0 --use-min-nodes --nodes=3 --exclusive'

        template_slurm = utils.AtomicFile("recon.template.slurm.sh")
        template_slurm.replace(MATCHQSPEC, QSPEC)
        template_slurm.save(replace=True)

    rand_name = str(random.randint(0, 99999999)).zfill(8)
    workdir = "recon-run-{}-{}".format(datetime.date.today("%Y%m%d").strftime(), rand_name)
    jobname = rand_name

    os.mkdir(workdir)
    print("Correcting permissions...please wait")
    for projdir in projDirs:
        os.symlink(projdir, os.path.join(workdir, projdir))
        runCmd("chgrp -R w09    {}/").format(projdir)
        runCmd("chmod -R ug+rX  {}/").format(projdir)
        runCmd("chgrp  w09    {}/").format(projdir)
        runCmd("chmod  ug+rX  {}/").format(projdir)
        runCmd(
            '( cd "{}/{} " && cd `pwd -P` && chgrp w09 . && chmod ug+rx . && cd .. && chgrp w09 . && chmod ug+rx . )').format(
            workdir, projdir)
        runCmd('( cd "{}/{}" && chgrp w09 . && chmod ug+w . )').format(workdir, projdir)
        runCmd('cd "{}/{}" && chgrp w09 AlignmentParmVals.dat && chmod ug+w AlignmentParmVals.dat').format(workdir,
                                                                                                           projdir)
    print('Correcting permissions. Done.')
    runCmd('( cd "{}" && templateApplyIn.py prerun ../recon.template.in recon.template.in )').format(workdir)
    copyfile("recon.template.slurm.sh", "{}/recon.slurm.sh".format(workdir))

    runCmd('chgrp -R w09    "{}"'.format(workdir))
    runCmd('chmod -R ug+rwX    "{}"'.format(workdir))

    # TODO if MANGO_NO_LAUNCH_RECON

    FULLWORKDIR = getOSCommand("`pwd - P` /$WORKDIR")

    runfile = utils.AtomicFile(os.path.join(parameters.GPURUNDIRECTORY, jobname))
    string = """#!/bin/bash
                ulimit -S -c 0
                 cd '$FULLWORKDIR' \\
                 && echo `date` 'sbatch ./recon.slurm.sh' >> _queued_ \\
                 && sbatch --job-name=$JOBNAME ./recon.slurm.sh >> _queued_ \\
                 && echo `date` 'sbatch reconPostrun.py' >> _queued_ \\
                 && sbatch --job-name=$JOBNAME reconPostrun.py >> _queued_ \\
                 && echo "`date`: reconstruct queued GPU" >> ../STATUS_RECON.txt \\
                 || echo "`date`: FAILED: reconstruct queue GPU" >> ../STATUS_RECON.txt"""
    runfile.write("#!/bin/bash")
