
import sys
import os
from shutil import copyfile


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
    isSFT
    isTall #TODO
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
        projSizeGB =