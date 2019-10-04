
import os
import glob
import numpy as np
import re
import stat
import json
def save_json(dic):
    """
    To save dic into stage file.
    :param dic:
    :return:
    """
    stage_file = "stage"
    init_data_file_tmp = os.path.join(stage_file  + ".tmp")
    init_data_file = os.path.join(stage_file + ".json")
    with open() as f:
        json.dump(dic, f)
    os.rename(init_data_file_tmp, init_data_file)

def writeToJson(json_dir,stage,dic):
    file_tmp = os.path.join(json_dir, stage+ ".tmp")
    file_final = os.path.join(json_dir, stage + ".json")
    with open() as f:
        json.dump(dic, f)
    os.rename(file_tmp, file_final)

def load_json(json_dir,stage):
    stage_file = "stage"
    initfilepath = os.path.join(stage_file,".json")

    with open(initfilepath) as f:
        dic = json.loads(f)

    return dic





def onRaijin():
    return RunEnvironment().isPBS()

def runCmd(cmd):
    print("Submitting shell command: %s" % (cmd))
    subprocess.check_call(cmd, shell=True)
    print("Done with shell command: %s" % (cmd))

def setLaunchReconScript(script=None, mango_proj=None, mango_dir=None, mango_exe=None,
                         sh_name=None, copy2mdss=None, mdss_proj=None, stage=None):
    if script is None:
        script = os.getenv("SCRIPTNAME", "/home/110/xct110/bin/reconController.sh")
    if mango_proj is None:
        mango_proj = os.getenv("MANGO_PROJECT", "d59")
    if mango_dir is None:
        mango_dir = os.getenv("MANGO_DIR", "/home/110/xct110/bin")
    if mango_exe is None:
        mango_exe = os.getenv("MANGO_EXE", "mango")
    if sh_name is None:
        sh_name = os.getenv("SH_NAME", "reconController.sh")
    if copy2mdss is None:
        copy2mdss = os.getenv("COPY_TO_MDSS", "true")
    if mdss_proj is None:
        mdss_proj = os.getenv("MDSS_PROJECT", "w09")
    if stage is None:
        stage = os.getenv("STAGE", "init_get_data")
    with open('launchReconProgram.sh', 'w') as ff:
        ff.write("%s %s %s %s %s %s %s %s" 
            % (script, mango_proj, mango_dir, mango_exe, sh_name, copy2mdss, mdss_proj, stage))
    runCmd("chmod u+x launchReconProgram.sh")

def rsync(source, destination, numberOfAttempts=3):
    command = "rsync -av --no-p %s %s" % (source, destination)
    attempts = 0
    while attempts < numberOfAttempts:
        try:
            runCmd(command)
            # If the command succeeds, we can stop here.
            break
        except subprocess.CalledProcessError:
            attempts += 1
            if attempts == 3:
                print("Failed with %s attempts." % numberOfAttempts)
                raise

class RunEnvironment():

    def getReconLayout(self, ncpus=None):
        if ncpus is None:
            ncpus = self.getNCPUS()
        if onRaijin() and ncpus % 16 != 0:
            raise ValueError(
                "The number of CPUs %s is not divisible by 16: recon on Raijin cannot run without this condition being met." %(ncpus))
        # Want to find a layout that is: (i) as close to square as possible; and
        # (ii) such that x*y*z = ncpus; and (iii) z = 1.
        ncpux = next((ncpux for ncpux in range(
            int(np.sqrt(ncpus)) + 1, 0, -1) if ncpus % ncpux == 0), -1)
        ncpuy = ncpus // ncpux
        print("Using processor layout (x,y,z): %s : %s : %s (since %s * %s * %s = %s)" %
              (ncpux, ncpuy, 1, ncpux, ncpuy, 1, ncpus))
        return (ncpux, ncpuy, 1)

    def _checkEnvVars(self, listOfPossibilities, errMsg=""):
        for name in listOfPossibilities:
            if name in os.environ:
                return os.environ[name]
        raise KeyError("No recognised environment variable found for %s" % errMsg)

    def getNCPUS(self):
        return int(self._checkEnvVars(["PBS_NCPUS", "SLURM_NTASKS"], errMsg="NCPUS"))

    def getMemInGb(self):
        mem = self._checkEnvVars(["PBS_VMEM"], errMsg="memory")
        return int(mem) // (1024 * 1024 * 1024)

    def getNumNodes(self):
        return int(self._checkEnvVars(["SLURM_JOB_NUM_NODES", "SLURM_NNODES"], errMsg="NNODES"))

    def getNumCPUsPerNode(self):
        return self.getNCPUS() // self.getNumNodes()

    def runOnMPI(self, command, ncpus=None):
        if ncpus is None:
            ncpus = self.getNCPUS()
        runCmd("mpirun -np %s %s" % (ncpus, command))

    def isSLURM(self):
        return "SLURM_MPI_TYPE" in os.environ

    def isPBS(self):
        return "PBS_JOBID" in os.environ


class RunState():

    def __init__(self, runInSubdir=False):
        self.runInSubdir = runInSubdir

    def doOnGPU(self):
        doGPU = False
        fNames = glob.glob('proju16*_raw/expt_tomo.in')
        if len(fNames) == 0:
            fNames = glob.glob('expt_tomo.in')
        for fName in fNames:
            with open(fName) as inFile:
                doGPU = any(re.match("\s+iterative_trajectory\s+true\s+", line) for line in inFile)
            if doGPU:
                return doGPU
        return doGPU

    def imageWidth(self):
        width = 0
        fNames = glob.glob('proju16*_raw/expt_tomo.in')
        if len(fNames) == 0:
            fNames = glob.glob('expt_tomo.in')
        for fName in fNames:
            with open(fName) as inFile:
                for line in inFile:
                    if "image_width" in line:
                        width = max(width, int(line.split()[-1]))
        if width == 0:
            return None
        return width

    def voxelsXYZ(self):
        largestVoxelCount = 0
        largestXYZ = [0, 0, 0]
        fNames = glob.glob('proju16*_raw/expt_tomo.in')
        if len(fNames) == 0:
            fNames = glob.glob('expt_tomo.in')
        for fName in fNames:
            with open(fName) as inFile:
                for line in inFile:
                    if "num_voxels" in line:
                        xyz = ('>' + line.split()[-1] + '<').split('><')[1:4]
                        xyz = [int(i) for i in xyz]
                        totalVoxels = xyz[0] * xyz[1] * xyz[2]
                        if totalVoxels > largestVoxelCount:
                            largestVoxelCount = totalVoxels
                            largestXYZ = xyz
        return largestXYZ

    def getSampleName(self):
        if self.runInSubdir:
            return os.path.split(os.path.split(os.getcwd())[0])[1]
        else:
            return os.path.split(os.getcwd())[1]

    def getProjectName(self):
        if self.runInSubdir:
            return os.path.split(os.path.split(os.path.split(os.getcwd())[0])[0])[1]
        else:
            return os.path.split(os.path.split(os.getcwd())[0])[1]

    def _getFlagFilename(self, flag):
        return "___%s_OK___" % (flag)

    def getFlagState(self, flag):
        return os.path.exists(self._getFlagFilename(flag))

    def setFlag(self, flag, state):
        if state is self.getFlagState(flag):
            return
        elif state is True:
            open(self._getFlagFilename(flag), 'a').close()
        elif state is False:
            os.remove(self._getFlagFilename(flag))
        else:
            raise TypeError(
                "The state value for a flag can only, at present, be set to True or False, not %s."
                 % (state))

    def isROI(self):
        return "ROI" in self.getSampleName()

    def getWorkDir(self):
        return os.getcwd()

    def getMangoPath(self):
        try:
            mango = os.environ["MANGO_DIR"] + "/" + os.environ["MANGO_EXE"]
        except KeyError as err:
            print("A system variable is not set.")
            raise
        if not os.path.isfile(mango):
            raise RuntimeError("Nothing at the path %s specified by MANGO_DIR and MANGO_EXE"
                % mango)
        return mango


class ReconTemplate():

    def __init__(self, templateName, templateLocation=None, localName=None):
        if templateLocation is None:
            templateLocation = os.environ["MANGO_DIR"]
        if localName is None:
            localName = templateName
        self.src = templateLocation + "/" + templateName
        self.dst = "./" + localName
        if self.src == self.dst:
            raise ValueError(
                "The source (%s) and destination (%s) for the template install cannot be identical."
                 % (self.src, self.dst))
        if not os.path.isfile(self.src):
            raise ValueError(
                "The source template %s does not exist, or is not a file." %
                (self.src))
        self.replaceRegex = []
        self.replacements = {}
        self.filesToAppend = []

    def install(self, replacements=None, replaceRegex=None, overwrite=True):
        if replacements is None:
            replacements = {}
        replacements.update(self.replacements)
        if replaceRegex is None:
            replaceRegex = self.replaceRegex
        if overwrite is False and os.path.isfile(self.dst):
            print("A copy of the template file already exists in the destination %s" % self.dst)
            return
        with open(self.src) as infile:
            intxt = infile.read()
        for regexPair in replaceRegex:
            match = regexPair[0]
            replace = regexPair[1]
            intxt = re.sub(match, r'\g<1>' + str(replace) + r'\g<3>', intxt, flags = re.MULTILINE)
        for tag, value in replacements.iteritems():
            intxt = intxt.replace(tag, str(value))
        with open(self.dst, 'w') as outfile:
            outfile.write(intxt)
        for appendFile in self.filesToAppend:
            with open(appendFile) as srcFile, open(self.dst, 'a') as dstFile:
                dstFile.write(srcFile.read())
        os.chmod(self.dst, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

    def unInstall(self):
        if os.path.isfile(self.dst):
            os.remove(self.dst)
