import fnmatch
import os


class InsufficientDFFiles(Exception):
    pass


class InsufficientCFFiles(Exception):
    pass


class InsufficientHlxFiles(Exception):
    pass


class InsufficientFiles(Exception):
    pass


def checkfiles(remotedir, workdir):
    if not fnmatch.fnmatch(workdir, "*proj*"):
        print("skip check not a projection directory")
        return 0

    with open(os.path.join(workdir, "tomo.in")) as f:  # TODO dont know this file's name

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

    if do_camera_x_shift:
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
        raise InsufficientDFFiles
    if numCfFiles < num_clear_fields:
        raise InsufficientCFFiles
    if numPrjFiles < total_num_projections:
        raise InsufficientHlxFiles
    if numPrjFiles < 40:
        raise InsufficientFiles

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