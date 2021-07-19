import xarray as xr
from datetime import datetime,timedelta
import numpy as np
import pandas as pd



def HARM_to_LES(df,date,dt):
    #
    # Needs several steps to convert 
    #
    # 1.) deaccumulate tendencies
    # 2.) average over domain
    # 3.) calculate pressure
    # 4.) rename variables 
    # 5.) calculate z 
    # 6.) get 25 hr subset 
    #
    
    ## avaerage over domain ##

#    df = df.mean(dim=('x','y'))

    ## 1.) deaccumulate tendencies ##

    # define new arrays
    dtq_dyn = np.zeros((df.dtq_dyn.values).shape)
    dtT_dyn = np.zeros((df.dtq_dyn.values).shape)
    dtu_dyn = np.zeros((df.dtq_dyn.values).shape)
    dtv_dyn = np.zeros((df.dtq_dyn.values).shape)
    dtqc_dyn = np.zeros((df.dtq_dyn.values).shape)

    # loop through time to deaccumulate depending on difference in time-bounds
    for t in range(0,len(df.time)):
        
        time_bnds = df.time_bnds.values[t,:]
        timediff = (time_bnds[-1]-time_bnds[0]).astype('timedelta64[s]') # convert to seconds

        if timediff <= timedelta(seconds=3600):
            dtq_dyn[t,:] = df.dtq_dyn[t,:]/dt
            dtT_dyn[t,:] = df.dtT_dyn[t,:]/dt
            dtu_dyn[t,:] = df.dtu_dyn[t,:]/dt
            dtv_dyn[t,:] = df.dtv_dyn[t,:]/dt
            dtqc_dyn[t,:] = df.dtqc_dyn[t,:]/dt
        else:
            dtq_dyn[t,:] = (df.dtq_dyn[t,:] - df.dtq_dyn[t-1,:])/dt
            dtT_dyn[t,:] = (df.dtT_dyn[t,:] - df.dtT_dyn[t-1,:])/dt
            dtu_dyn[t,:] = (df.dtu_dyn[t,:] - df.dtu_dyn[t-1,:])/dt
            dtv_dyn[t,:] = (df.dtv_dyn[t,:] - df.dtv_dyn[t-1,:])/dt
            dtqc_dyn[t,:] = (df.dtqc_dyn[t,:] - df.dtqc_dyn[t-1,:])/dt

    # replace accumulated tendencies with deaccumulated tendencies 

    df['dtq_dyn'] = xr.DataArray(data=dtq_dyn,dims = dict(time = df.time, lev = df.lev, x=df.x,y=df.y))
    df['dtT_dyn'] = xr.DataArray(data=dtT_dyn,dims = dict(time = df.time, lev = df.lev, x=df.x,y=df.y))
    df['dtu_dyn'] = xr.DataArray(data=dtu_dyn,dims = dict(time = df.time, lev = df.lev, x=df.x,y=df.y))
    df['dtv_dyn'] = xr.DataArray(data=dtv_dyn,dims = dict(time = df.time, lev = df.lev, x=df.x,y=df.y))
    df['dtqc_dyn'] = xr.DataArray(data=dtqc_dyn,dims = dict(time = df.time, lev = df.lev, x=df.x,y=df.y))

    ## average over domain ##

    df = df.mean(dim=('x','y'))

    ##### calculate pressure #####

    ahalf= (pd.read_csv('/nfs/home/users/theeuwes/work/DALES_runs/ecf/scr/data/H43_65lev.txt',
                         header=None,index_col=[0],delim_whitespace=True))[1].values[:]
    bhalf= (pd.read_csv('/nfs/home/users/theeuwes/work/DALES_runs/ecf/scr/data/H43_65lev.txt',
                         header=None,index_col=[0],delim_whitespace=True))[2].values[:]

    ph = np.array([ahalf + (p * bhalf) for p in df['ps'].values])
    p = np.zeros((df.ta.values).shape)
    for z in range(0,len(df.lev)):
        p[:,z] = 0.5 * (ph[:,z] + ph[:,z+1])
    
    df['p'] =  xr.DataArray(data=p,dims = dict(time = df.time, lev = df.lev))
    
    ##### rename variables #####

    df = df.rename({'ua':'u', 'va':'v', 'ta':'T', 'hus': 'q', 'ps':'p_s', 'lev':'level'})
    
    # create dummy for T_s and qt_s
    df['ql'] = xr.zeros_like(df.q)
    df['T_s'] = xr.zeros_like(df.p_s)
    df['q_s'] = xr.zeros_like(df.p_s)

    df['T_s'] = df.T.isel(level=-1)
    df['q_s'] = df.q.isel(level=-1)

    print(df.T_s.values,df.q_s.values)
    ##### calculate height #####

    df['z'] = df.phi / 9.81

    ##### flip z dimension #####
    
    df = df.sel(level=slice(None,None,-1))
     
    df =  df.sel(time = slice(None, datetime(date.year,date.month,date.day,23)+timedelta(seconds=3600)))
    print(df)

    return df
