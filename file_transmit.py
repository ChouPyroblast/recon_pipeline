import sftp
import os
import argparse
import fnmatch
import datetime

"""
No batch
paramiko or os command line
timestamp
tmpfile - > final file
"""

parser = argparse.ArgumentParser(description="get experiment data from acquisition machines")
parser.add_argument("--comp", default="apmac40", help="Acquisition machine")
parser.add_argument("--user", default="appmaths", help="user of acquisition machine")
parser.add_argument("--root", default="/cygdrive/g/XCT_System", help="root of the data")
parser.add_argument("--password", help="password, used when ssh keys are not set ")
parser.add_argument("--pkey", default="", help="the location of private key")
args = parser.parse_args()

okfile = "AA_transfer_ok_xct.txt"

# Current dir check

cwd = os.getcwd()
if cwd.split(os.sep)[-3] != "recon_ws":
    print("Fatal: Must be run from within recon_ws/project/sample")
    exit(1)

sample = cwd.split(os.sep)[-1]
project = cwd.split(os.sep)[-2]

client = sftp.Ftpclient(args.comp, 22)

if args.password:
    flag = client.connect(username=args.user, password=args.password)
    if not flag:
        print("no connection")
        exit(1)
else:
    flag = client.connect(username=args.user, pkey=args.password)
    if not flag:
        print("no connection")
        exit(1)


def getFiles(remotedir, workdir):
    # Todo check weather files or dir
    print("mkdir ./workdir")
    try:
        os.mkdir()
    except NotImplementedError:
        exit(6)
    # get remote fileList
    excludelist = ["*snap.raw", "*snap??.raw", "snap*.raw", "*_TEST*.raw", "test*.raw", "*~", "*png"]
    print("obtain all expected remote files")
    remoteFileList = client.list_dir(os.path.join(args.root, project, sample, remotedir))
    if not remoteFileList:
        exit(7)
    for file in remoteFileList:
        delete_flag = 0
        for pattern in excludelist:
            if fnmatch.fnmatch(file, pattern):
                delete_flag = 1
                break
        remoteFileList.remove(file)

    # get local fileList
    print("ls -l" + workdir)
    localFileList = os.listdir("./workdir")

    # list files that remain to be copied over from remote to local
    filesToCopy = list(set(remoteFileList).difference(set(localFileList)))

    # copy blocks of files using sftp (checking for success after each block)

    blockSize = 100
    numFiles = len(filesToCopy)
    if numFiles:
        print("LOG: Number of file(s) to transfer = " + str(numFiles))
    else:
        print("WARNING: No files to transfer")


    failureCount = 0
    recentFailureCount = 0

    while i < numFiles:
        exitCode = client.download(os.path.join(args.root, project, sample, remotedir, filesToCopy[i]), "./workdir")
        if exitCode:
            i = i + 1
            if recentFailureCount > 0:
                recentFailureCount = recentFailureCount - 1
        else:
            failureCount = failureCount + 1
            recentFailureCount = recentFailureCount + 3

        if recentFailureCount > 100:
            print("Error Too many transfer failures")
            exit(15)


def checkFiles(remotedir, workdir):
    if not fnmatch.fnmatch(workdir, "*proj*"):
        print("skip check not a projection directory")
        return 0
    with open(os.path.join(workdir, "tomo.in")) as f:  # todo dont know this file's name

        # check all projs copied.
        # num_dark_fields =

        for line in f:
            if "num_dark_fields" in line:
                num_dark_fields = int(line.split()[1])
            if "num_clear_fields" in line:
                num_clear_fields = int(line.split()[1])
            if "do_auto_clearfields" in line:
                do_auto_clearfields = bool(line.split()[1])

            if "clearfield_type" in line:
                clearfield_type = bool(line.split()[1])

            if "do_camera_x_shift" in line:
                do_camera_x_shift = bool(line.split()[1])
            if "camera_x_shift_columns" in line:
                camera_x_shift_columns = int(line.split()[1])
            if "total_num_projections" in line:
                total_num_projections = int(line.split()[1])
    if do_auto_clearfields:
        if clearfield_type == "both":
            num_clear_fields = 2 * num_clear_fields

    if do_camera_x_shift:  ############## high risk block
        print("do_camera_x_shift parameter camaera_x_shift_columns =" + camera_x_shift_columns)
        camera_x_shift_columns = 2 * camera_x_shift_columns + 1
        num_clear_fields = camera_x_shift_columns * num_clear_fields

    print("Expected number of DF is " + str(num_dark_fields))
    print("Expected number of CF is " + str(num_clear_fields))
    print("Expected number of projections is " + str(total_num_projections))

    files = os.listdir(workdir)

    numDFFiles = 0
    numCfFiles = 0
    numHlxFiles = 0
    numCircFiles = 0

    max_imgsize = 0

    for file in files:
        if file.endswith(".raw") and "expt_DF" in file:
            numDFFiles = numDFFiles + 1
        if file.endswith(".raw") and "expt_CF" in file:
            numCfFiles = numCfFiles + 1
        if file.endswith(".raw") and "expt_H" in file:
            numHlxFiles = numHlxFiles + 1
        if file.endswith(".raw") and "expt_0" in file:
            numCircFiles = numCircFiles + 1
        if fnmatch.fnmatch(file, "expt*[0-9][0-9][0-9].raw"):
            max_imgsize = max(max_imgsize, os.path.getsize(os.path.join(workdir, file)))

    numPrjFiles = numHlxFiles + numCircFiles

    if numDFFiles < num_dark_fields:
        print("ERROR Insufficient DF files.")
        return 0
    if numCfFiles < num_clear_fields:
        print("ERROR Insufficient CF files.")
        return 0
    if numPrjFiles < total_num_projections:
        print("ERROR Insufficient projection files.")
        return 0
    if numPrjFiles < 40:
        print("ERROR: Very few, or zero projection files.")
        return 0

    # check for corrupted files, rename to allow retry.

    incompleteFileList = []
    for file in files:
        if os.path.getsize(os.path.join(workdir, file)):
            incompleteFileList.append(file)

    if not incompleteFileList:
        problemFileCount = len(incompleteFileList)
        if problemFileCount < 30:
            print("The following files seem to be incomplete, will retry:")
            for file in incompleteFileList:
                os.remove(os.path.join(workdir, file), )
        else:
            print("FATAL: The following files seem to be incomplete, too many problems terminating.")
            for file in incompleteFileList:
                print(file)
            return 0


def markComplete(remotedir, workdir):
    with open(okfile, "w") as f:
        f.write(str(datetime.datetime.now()))
        with os.scandir(workdir) as dir_entries:
            for entry in dir_entries:
                filename = entry.name
                info = entry.stat()
                f.write(info.st_size + " " + info.st_mtime + " " + filename)

    client.upload(os.path.join(workdir, okfile), os.path.join(args.root, project, sample, remotedir))


# MAIN
print("Checking what type of data is on the remote computer")

# Todo projSubTxt=$(ssh ${ACQCOMPUSER}@$ACQCOMP "cd '$ACQCOMPROOT/$project/$sample' && head -n1 proju16*_raw.txt 2>/dev/null | tr -d '\r'" | awk 'BEGIN {FS="/"; OFS="\t"}  (!/^=/ && !/^$/) {print LAST, "../"$NF} (/^=/) {gsub("^==> ","",$0); gsub("\\.txt <==$","",$0); LAST=$0}' )

projsubdirs = []
rawFilesExist = []
for subdir in client.list_dir(os.path.join(args.root, project, sample)):
    if fnmatch.fnmatch(subdir, "proju16*_raw/"):  # todo hard-code
        projsubdirs.append(subdir)
    if fnmatch.fnmatch(subdir, "*0000.raw"):
        rawFilesExist.append(subdir)

sources = []
destinations = []

if projsubdirs:
    for subdir in projsubdirs:
        sources.append(subdir)
        destinations.append(subdir)
    sources.append(".")
    destinations.append(".")
elif rawFilesExist:
    sources.append(".")
    destinations.append("proju16_raw")  # todo hard-code
else:
    print("No suitable directory structure found on remote, expecting .raw files or proju16 subdirectories")
    exit(2)

print("remove pre-existing empty projection directories")
os.removedirs("proju16*_raw")

for i in range(len(sources)):
    print("get files from sources" + sources[i] + "to destionation" + destinations[i])
    getFiles(sources[i], destinations[i])
checkOK = 0
for i in range(len(sources)):
    print("get files from sources" + sources[i] + "to destionation" + destinations[i])
    if not checkFiles(sources[i], destinations[i]):
        checkOK = 1
        break

if checkOK:
    print("FATAL: get_data has not provided a complete set of consistent files.")
    exit(1)
else:
    for i in range(len(sources)):
        print("markComplete: " + sources[i] + destinations[i])
        markComplete(sources[i], destinations[i])
    exit(0)

exit(2)
