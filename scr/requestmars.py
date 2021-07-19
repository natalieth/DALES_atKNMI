#!/usr/bin/env python3

import os
import datetime
import sys

def ec_soil(path,date):
    import os
    from ecmwfapi import ECMWFService
  
    server = ECMWFService("mars")
    server.execute(
       {
       "class":"od",
       "expver":"1",
       "stream": "oper",
       "date": "{0:04d}-{1:02d}-{2:02d}".format(date.year,date.month,date.day),
       "area": "52.971/3.927/50.971/5.927",
       "grid": "0.3/0.3",
       "levtype": "sfc",
       "type": "an",
       "time": "00:00:00",
       "param": "39.128/40.128/41.128/42.128/139.128/170.128/183.128/236.128/43.128"
       },"{0}soil_{1:04d}{2:02d}{3:02d}.grib".format(path,date.year,date.month,date.day))
    
    os.system("grib_to_netcdf {0}soil_{1:04d}{2:02d}{3:02d}.grib -o {0}soil_{1:04d}{2:02d}{3:02d}.nc"
            .format(path,date.year,date.month,date.day))


if __name__ == '__main__':
    #
    # arg (1) :: date YYYYMMDD
    #
    
    argv = sys.argv[1]  # date yyyy-mm-dd
    date = datetime.datetime.strptime(argv,'%Y%m%d')

    path = "/nfs/home/users/theeuwes/work/LES_forcings/IFS_SOIL/"
    
    if os.path.isfile("{0}soil_{1:04d}{2:02d}{3:02d}.nc"
            .format(path,date.year,date.month,date.day)):
        print("file already exists!")
    else: 
        ec_soil(path,date)


