
import sys
import os
from shutil import copyfile
from utils import getOSCommand

dic = utils.load_json("stage.json")


def recon():


    if dic["data_only"]:
        sys.exit(0)

    #if dic["project"] == "DeBeers" or dic["project"] == "Testing_Mk2" :
        # TODO
    #    pass


    #queueOnGPU
    os.system('echo "`date`: pipeline handover to GPU" >> STATUS_RECON.txt')
    reconSystem=GPU

    isAxialROI = os.path.isdir("proju16_roi_raw") and os.path.isdir("proju16_overview_raw")
    isSFT = getOSCommand("cat proju16_raw/expt*.in | tr -d '\r' | grep -m1 iterative_trajectory | awk '{print $2}'")=="true"

    isTall = getOSCommand("cat proju16_raw/expt*.in | tr -d '\r' | grep -m1 num_voxels| awk '{print $2}' | awk 'BEGIN "
                          '{FS="[<>]+"}' 
                          " ($4/($2+$3) > 1.5) {print true} (!($4/($2+$3) > 1.5)) {print false} '")
    reconType = dH

    if isAxialROI:
        reconType = SFT_AxialROI
        projDirs = ("proju16_roi_raw","proju16_overview_raw")
    elif isSFT:
        reconType = SFT
    elif isTall:
        reconType = dH_pcm

    TEMPLATEDIR = os.path.join(dic[mango_dir],templates)
    if not os.isfile("recon.template.in"):
        srcfilename = "{}/recon.{}_{}.template.in".format(TEMPLATEDIR,reconSystem,reconType)
        destname = "recon.template.in"
        copyfile(srcfilename,destname)
    if not os.isfile("recon.template.slurm.sh"):
        srcfilename = "{}/recon.{}_{}.template.slurm.sh".format(TEMPLATEDIR, reconSystem, reconType)
        destname = "recon.template.slurm.sh"
        copyfile(srcfilename,destname)
        projSizeGB = getOSCommand("du --apparent-size --block-size=1G -s ${projDirs[0]}/ | sed 's#\s.*$##'")
        memNeededGB = projSizeGB*15
        MATCHQSPEC = '--partition=gpucluster0'
        QSPEC = MATCHQSPEC
        if isAxialROI:
            if memNeededGB<500:
                QSPEC='--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --nodes=1 --exclusive'
            elif memNeededGB<1000:
                QSPEC = '--partition=gpucluster0,LOgpu8_15_A,LOgpu8_15_B --use-min-nodes --constraint=[gpu2A*1\&gpu2B*1] --exclusive'
            elif memNeededGB<1500:
                QSPEC = '--partition=gpu8_15_A,gpu8_15_B,LOgpucluster0,LOgpu8_30_A --use-min-nodes --constraint=[gpu3A*1\&gpu3B*1\&gpu3C*1] --exclusive'
            elif  memNeededGB<2800:
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
