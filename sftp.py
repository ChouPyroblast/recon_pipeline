import paramiko
import os


def byte_count(xfer, to_be_xfer):
    print(" transferred: {0:.0f} %".format((xfer / to_be_xfer) * 100))


class Ftpclient():

    def __init__(self, host, port=22):
        self.transport = paramiko.Transport((host, port))
        self.sftp = None

    def __del__(self):
        self.transport.close()
        self.sftp.close()

    def download(self, source, destination):
        try:
            self.sftp.get(localpath=destination + "-tmp", remotepath=source,
                          callback=byte_count)  # use tmp file in case of interrupt


            return 1
        except Exception as e:
            print(e)
            return 0

    def upload(self, source, destination):
        try:
            # sftp = paramiko.SFTPClient.from_transport(transport)
            self.sftp.put(localpath=source, remotepath=destination, callback=byte_count)
            # sftp.close()
            return 1
        except Exception as e:
            print(e)
            return 0

    def connect(self, username, pkey=None, password=None):

        try:
            if password is not None:
                self.transport.connect(username=username, password=password)
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            else:
                self.transport.connect(username=username, pkey=pkey)
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            return 1
        except Exception as e:
            print(e)
            return 0

    def list_dir(self, dir):
        try:
            return self.sftp.listdir(dir)
        except Exception as e:
            print(e)
            return 0

    def listdir_attr(self, dir):
        try:
            return self.sftp.listdir_attr(dir)
        except Exception as e:
            print(e)
            return 0

    def read_file(self, file):
        try:
            return self.sftp.file(file)
        except Exception as e:
            print(e)
            return 0
