import sftp
import os
import argparse
import fnmatch
import datetime
import time
import read_data
import zlib
import sys

# TODO the termination condition

parser = argparse.ArgumentParser(description="get experiment data from acquisition machines")
parser.add_argument("--comp", default="appc59.anu.edu.au", help="Acquisition machine")
parser.add_argument("--user", default="user", help="user of acquisition machine")
parser.add_argument("--root", default="/cygdrive/d/CT_Data/", help="root of the data")
parser.add_argument("--workdir", default="proju16_raw", help="the destination of files")
parser.add_argument("--remotedir", default=".", help="the source of the files on server")
parser.add_argument("--password", default="Kent", help="password, used when ssh keys are not set ")
parser.add_argument("--pkey", default="", help="the location of private key")
parser.add_argument("--waittime", default=50, help="the waiting time for when there is no new file")
args = parser.parse_args()
cwd = os.getcwd()

# obtain working dir,proj,sample

if cwd.split(os.sep)[-3] != "test_transfer":
    print("Fatal: Must be run from within recon_ws/project/sample")
    sys.exit(2)
sample = cwd.split(os.sep)[-1]
project = cwd.split(os.sep)[-2]

client = sftp.Ftpclient(args.comp, 22)

# password or private keys
if args.password:
    flag = client.connect(username=args.user, password=args.password)
    if not flag:
        print("no connection")
        sys.exit(1)
else:
    flag = client.connect(username=args.user, pkey=args.password)
    if not flag:
        print("no connection")
        sys.exit(1)

remotedir = args.remotedir
workdir = args.workdir
if not os.path.isdir(workdir):
    os.mkdir(workdir)
from collections import defaultdict

file_counter = defaultdict(lambda: 0)
log = {}
log_name = "saved_files.log"
remotelog_name = "saved_files.log"
expt_name = "expt_tomo.in"
if os.path.isfile(log_name):
    log_file = open(log_name)
    for line in log_file:
        s = line.split(" ")  # read log into a dic
        file_counter[s[0][:6]] = file_counter[s[0][:6]] + 1
        print(s)
        log[s[0]] = (s[1])  # only read file name and its modified time
    log_file.close()
    log_file = open(log_name, "a")
else:
    log_file = open(log_name, "w")
    # log_file.write("\t".join("name","mtime(float)","size",finish_localtime,mtime(yy-MM-dd--hh--mm-ss))

# to obtain how many files are expected.
exptfile = client.read_file(os.path.join(args.root, project, sample, remotedir, expt_name))
expt_counter = defaultdict(lambda: 0)

if exptfile:
    lines = exptfile.read().decode("utf-8", errors='ignore').rstrip().split("\n")

    exptfile.close()
else:
    print("Cannot find expt file!")
    sys.exit(2)
expt = read_data.read_file_flat(lines)

expt_counter["num_dark_fields"] = expt["num_dark_fields"]
expt_counter["num_clear_fields"] = expt["num_clear_fields"]

if expt["do_auto_clearfields"] == "true":
    if expt["clearfield_type"] == "both":
        expt_counter["num_clear_fields"] = expt_counter["num_clear_fields"] * 2
        expt_counter["num_dark_fields"] = expt_counter["num_dark_fields"] * 2
if expt["do_camera_x_shift"] == "true":
    expt_counter["num_clear_fields"] = expt_counter["num_clear_fields"] * (2 * expt["camera_x_shift_columns"] + 1)
expt_counter["total_num_projections"] = expt["total_num_projections"]

# variables controls loop
max_access_times = 100
i = 0
notask = 0
errorcount = 0
taskcounter = 0
while i < max_access_times:
    sleepflag = True
    # collect which files finish acquisition
    remotelog = client.read_file(os.path.join(args.root, project, sample, remotedir, remotelog_name))
    if remotelog:
        lines = remotelog.read().decode("utf-8").rstrip().split("\n")  # todo record read lines
        remotelog.close()
    else:
        print("Fatal. Cannot open remote log ")
        errorcount = errorcount + 1
        continue
    readyfiles = {}  # this dict contains files that finish acquisition and its checksum
    excludelist = ["*snap.raw", "*snap??.raw", "snap*.raw", "*_TEST*.raw", "test*.raw", "*~", "*png"]
    for line in lines:
        s = line.rstrip().split(" ")

        flag = True  # flag to make sure the file is not in the excludelist
        for pattern in excludelist:
            if fnmatch.fnmatch(s[0], pattern):
                flag = False
                break
        if flag:
            readyfiles[(s[0])] = s[1]

    # list all files in remote dir
    files = client.listdir_attr(os.path.join(args.root, project, sample, remotedir))
    if not files:
        print("connection error")
        errorcount = errorcount + 1
        continue

    for file in files:
        # obtain file info
        filename = file.filename
        filemode = file.st_mode
        file_atime = file.st_atime
        file_mtime = file.st_mtime
        file_size = file.st_size
        if filename in readyfiles:
            if filename not in log or readyfiles[filename] != (
                    log[filename]):  # if this file is not on local or need updating
                sleepflag = False
                file_destination = os.path.join(workdir, filename)  # the downloaded file
                if client.download(os.path.join(args.root, project, sample, remotedir, filename), file_destination):
                    # checksum
                    with open(file_destination + "-tmp", "rb") as file_to_check:
                        # read contents of the file
                        data = file_to_check.read()
                        # pipe contents of the file through
                        crc32_returned = "{:x}".format(zlib.crc32(data) & 0xffffffff).upper()
                        print(crc32_returned)
                    # verified, modify modified time and write log
                    if crc32_returned == readyfiles[filename]:
                        os.rename(file_destination + "-tmp", file_destination)
                        print("download successfully and CRC32 verified!")
                        os.utime(file_destination, (file_atime, file_mtime))
                        log[filename] = crc32_returned
                        # write log

                        log_file.write(" ".join(
                            (filename, crc32_returned, str(file_mtime), str(file_size),
                             str(datetime.datetime.now()), str(datetime.datetime.fromtimestamp(file_mtime)))))
                        log_file.write("\n")
                        errorcount = errorcount - 1
                        file_counter[filename[:6]] = file_counter[filename[:6]] + 1
                        taskcounter = taskcounter + 1
                        print(str((taskcounter)) + " were downloaded")
                    else:
                        print("crc32 verification failed!")
                        os.rename(file_destination + "-tmp", file_destination)
                        errorcount = errorcount + 1
                        continue
                else:
                    print("download error")
                    errorcount = errorcount + 1
                    continue

    if expt_counter["num_dark_fields"] == file_counter["expt_D"] and expt_counter["num_clear_fields"] == file_counter[
        "expt_C"] and expt_counter["total_num_projections"] == file_counter["expt_H"] + file_counter["expt_0"]:
        print("all files copied. exit")
        sys.exit(1)

    if sleepflag:  # if no files are downloaded, wait for 30 sec
        print("no files are downloaded, wait for 30 sec")
        time.sleep(args.waittime)
        notask = notask + 1
    else:
        notask = 0

    if notask > 50:  # wait for too long time. Quit.
        print("There is no task for too long time, quit")
        sys.exit(1
    if errorcount > 50:
        print("Too much errors")
        sys.exit(1)
    i = i + 1
