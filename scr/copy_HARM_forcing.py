#!/usr/bin/env python3

import os 
import sys 
import shutil
import datetime


if __name__ == '__main__':
    argv = sys.argv[1]  # date yyyymmdd
    date = datetime.datetime.strptime(argv,'%Y%m%d')

    HH = 0
    source_path = "/dpsp/production/harmonie/43h211/"
    path = "/nfs/home/users/theeuwes/work/LES_forcings/HA43_CABAUW/"

    files = ["HA43_CABAUW_{0:04d}{1:02d}{2:02d}{3:02d}00_HIS.nc"
              .format(date.year,date.month,date.day,HH) ,
              "HA43_CABAUW_{0:04d}{1:02d}{2:02d}{3:02d}00_FP.nc"
              .format(date.year,date.month,date.day,HH)]


    # check if files are already in the desired directory

    if os.path.isfile(path+files[0]) & os.path.isfile(path+files[1]):

        print("file already exists!")

    else:
        try:
            # copy files over from TMP directory 
            shutil.copy(source_path+files[0],path)
            shutil.copy(source_path+files[1],path)
        except IOError:
            source_path_ws = "theeuwes@pc200248:/nobackup/users/theeuwes/testbed/HARMONIE/cabauw_forcings/"
            os.system("rsync -vau {} {}".format(source_path_ws+files[0],path))
            os.system("rsync -vau {} {}".format(source_path_ws+files[1],path))


