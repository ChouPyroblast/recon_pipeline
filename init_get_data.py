import os
def init_get_data():
    if

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
        currentUser = ""
        if currentUser != #*:
            print("Looker for data in {}@{}:{}/{}/{}".format(currentUser,currentComputer,currentRoot,project,sample))
            flag = os.system("")