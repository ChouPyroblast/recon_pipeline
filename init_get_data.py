import os
import recon
import json
import sys
import utils
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
    dic = utils.load_json(recon.json_dir ,recon.init_data_filename)


    if os.path.exists(""):
        pass

    acq_comp = None;
    acqcom_user= None;
    acqcom_root = None;
    currentRoot = "g/data2/w09/CT_Data"


    #TODO some code is deleted here.

    home = os.getenv("HOME")
    f = open(os.path.join(home,".reconControllerComputerList"))

    s = f.readline()
    while s:#TODO check reconControllerComputerList
        s = f.readline()
        currentUser = "" #TODO
        currentComputer = "";
        currentRoot = "";
        if currentUser != "#*":
            print("Looker for data in {}@{}:{}/{}/{}".format(currentUser,currentComputer,currentRoot,proj,sample))
            if not os.system("ssh $currentUser @$currentComputer test - d $currentRoot /$project /$sample"):
                acq_comp = currentComputer
                acqcom_root = currentRoot
                acqcom_user= currentComputer
    if acq_comp == None:
        print("couldn't find project/sample name")
        return False

    dic = {}
    dic[""] =
    dic[""]

    json .


    return True


