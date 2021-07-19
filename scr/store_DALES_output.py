#!/usr/bin/env python3

import os 
import sys
import glob 
import shutil
import datetime


if __name__ == '__main__':
    argv = sys.argv[1]  # date yyyymmdd
    date = datetime.datetime.strptime(argv,'%Y%m%d')
    
    exp = int(sys.argv[2])  # experiment number:: 1
    run_path = "/nfs/home/users/theeuwes/work/DALES_runs/{0:04d}{1:02d}{2:02d}/".format(date.year,date.month,date.day)
    store_path = "/nfs/home/users/theeuwes/work/testbed/DALES/{0:04d}/{1:02d}/{2:02d}/".format(date.year,date.month,date.day)

    # make directories 

    if not os.path.exists(store_path):
        os.makedirs(store_path)
 
    filesA = [run_path+'profiles.{0:03d}.nc'.format(exp),
              run_path+'tmser.{0:03d}.nc'.format(exp),
              run_path+'namoptions.{0:03d}'.format(exp),]
    to_filesA = [store_path+'profiles.{0:03d}.{1:04d}{2:02d}{3:02d}.nc'.format(exp,date.year,date.month,date.day),
              store_path+'tmser.{0:03d}.{1:04d}{2:02d}{3:02d}.nc'.format(exp,date.year,date.month,date.day),
              store_path+'namoptions.{0:03d}.{1:04d}{2:02d}{3:02d}'.format(exp,date.year,date.month,date.day),]
    
    for i,j in zip(filesA,to_filesA):
        print("Copying :", i)
        shutil.copy(i,j)
    
    filesB = glob.glob(run_path+"*{0:04d}{1:02d}{2:02d}.{3:03d}*.nc".format(date.year,date.month,date.day,exp))
    
    for i in filesB: 
        print("Moving :", i)
        shutil.move(i,store_path)
    



        

