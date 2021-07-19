#!/usr/bin/env python3

import numpy as np
import xarray as xr
import datetime
import shutil
import sys
import os

# Add src directory to Python path, and import DALES specific tools
src_dir = os.path.abspath('/nfs/home/users/theeuwes/work/DALES_runs/ecf/scr/')
sys.path.append(src_dir)
from DALES_tools import *
from harmonie_to_LESforcing import *
from IFS_soil import *
from slurm_scripts import create_runscript


def fbool(flag):
    """
    Convert a Python bool to Fortran bool
    """
    return '.true.' if flag==True else '.false.'



if __name__ == '__main__':
    # --------------------
    # Settings
    # --------------------
    argv = sys.argv[1]  # date yyyy-mm-dd
    date = datetime.datetime.strptime(argv,'%Y%m%d')


    print(date)
    expname     = 'cabauw_testbed'
    expnr       = 1       # DALES experiment number
    iloc        = 7+12    # Location in DDH/NetCDF files (7+12 = 10x10km average Cabauw)
    n_accum     = 1       # Number of time steps to accumulate in the forcings
    warmstart   = False   # Run each day/run as a warm start from previous exp
    auto_submit = False   # Directly submit the experiments (ECMWF only..)

    # 24 hour runs (cold or warm starts), starting at 00 UTC.
    start  = date
    dt_exp = datetime.timedelta(hours=24)   # Time interval between experiments
    end    = start + dt_exp
    t_exp  = datetime.timedelta(hours=24)   # Length of experiment
    eps    = datetime.timedelta(hours=1)

    # Paths to the LES forcings, and ERA5/Cabauw for soil initialisation
    path_HA = '/nfs/home/users/theeuwes/work/LES_forcings/HA43_CABAUW/'
    path_SO = '/nfs/home/users/theeuwes/work/LES_forcings/IFS_SOIL/'
    path_out = '/nfs/home/users/theeuwes/work/DALES_runs/'
 

    # ------------------------
    # End settings
    # ------------------------

    # Create stretched vertical grid for LES
    grid = Grid_stretched(kmax=160, dz0=20, nloc1=80, nbuf1=20, dz1=150)
    #grid.plot()

    date = start
    n = 30
    while date < end:
        print('-----------------------')
        print('Starting new experiment')
        print('-----------------------')

        # In case of warm starts, first one is still a cold one..
#        start_is_warm = warmstart and n>1
        start_is_warm = warmstart
        start_is_cold = not start_is_warm

        # Round start date (first NetCDF file to read) to the 3-hourly HARMONIE cycles
        offset = datetime.timedelta(hours=0) if date.hour%3 == 0 else datetime.timedelta(hours=-date.hour%3)
 
        # Get list of NetCDF files which need to be processed, and open them with xarray
#        nc_files = get_file_list(path, date+offset, date+t_exp+eps)
        nc_files = '{0:}/HA43_CABAUW_{1:04d}{2:02d}{3:02d}0000_*.nc'.\
                   format(path_HA, date.year, date.month, date.day)

        # Check if file actually exists..
        if not os.path.exists(nc_files):
            print('ERROR: Can not find input file {}'.format(nc_files))
            success = False

        try:
            nc_data  = xr.open_mfdataset(nc_files, combine='by_coords')
        except TypeError:
            nc_data  = xr.open_mfdataset(nc_files)
        
        print(nc_data)
        nc_data = HARM_to_LES(nc_data,date,3600)

        # Get indices of start/end date/time in `nc_data`
        t0, t1 = get_start_end_indices(date, date + t_exp + eps, nc_data.time.values)

        # Docstring for DALES input files
        domain    = 'cabauw' #nc_data.name[0,iloc].values
        lat       = 51.971
        lon       = 4.927
        docstring = '{0} ({1:.2f}N, {2:.2f}E): {3} to {4}'.format(domain, lat, lon, date, date + t_exp)
        
        print(nc_data.z)
        if start_is_cold:
            print('creating profiles!!')
            # Create and write the initial vertical profiles (prof.inp)
            create_initial_profiles_NForcing(nc_data, grid, t0, t1, docstring, expnr)

        # Create and write the surface and atmospheric forcings (ls_flux.inp, ls_fluxsv.inp, lscale.inp)
        create_ls_forcings_NForcing(nc_data, grid, t0, t1, docstring, n_accum, expnr, harmonie_rad=False)

        # Write the nudging profiles (nudge.inp)
        nudgefac = np.ones_like(grid.z)     # ?? -> set to zero in ABL?
        create_nudging_profiles_NForcing(nc_data, grid, nudgefac, t0, t1, docstring, 1, expnr)

        # Create NetCDF file with reference/background profiles for RRTMG
        create_backrad_NForcing(nc_data, t0, expnr)

        if start_is_cold:
            # Get the soil temperature and moisture from ERA5
            tsoil_ecmwf  = get_Tsoil_ERA5  (date, 4.9, 51.97, path_SO)
            phiw_ecmwf   = get_phisoil_ERA5(date, 4.9, 51.97, path_SO)
            type_ecmwf   = get_soiltype_ERA5(date, 4.9, 51.97, path_SO)
            z_soil       = [2.89,1.00,0.28,0.07]  # ecmwf operational model https://apps.ecmwf.int/codes/grib/param-db/?id=39

            # Option to re-scale soil moisture content
            type_soil, phi_soil = translate_to_cabauw(z_soil,type_ecmwf,phiw_ecmwf,src_dir+'/data/')            
          
        
        # Update namelist
        namelist = '{0}/data/namoptions.{1:03d}'.format(src_dir,expnr)
        replace_namelist_value(namelist, 'lwarmstart', fbool(start_is_warm))
        replace_namelist_value(namelist, 'lresettime', fbool(start_is_warm))
        replace_namelist_value(namelist, 'iexpnr',   '{0:03d}'.format(expnr))
        replace_namelist_value(namelist, 'runtime',  t_exp.total_seconds())
        replace_namelist_value(namelist, 'trestart', t_exp.total_seconds())
        replace_namelist_value(namelist, 'xlat',     lat)
        replace_namelist_value(namelist, 'xlon',     lon)
        replace_namelist_value(namelist, 'xday',     date.timetuple().tm_yday)
        replace_namelist_value(namelist, 'xtime',    date.hour)
        replace_namelist_value(namelist, 'kmax',     grid.kmax)
        replace_namelist_value(namelist, 'ltotruntime', fbool(start_is_warm))

        if start_is_cold:
            replace_namelist_value(namelist, 't_soil_p',       array_to_string(tsoil_ecmwf))
            replace_namelist_value(namelist, 'theta_soil_p',   array_to_string(phi_soil))
            replace_namelist_value(namelist, 'dz_soil',        array_to_string(z_soil))
            replace_namelist_value(namelist, 'soil_index_p',   array_to_string(type_soil))


#            replace_namelist_value(namelist, 'tsoildeepav', tsoil[-1])  #????
        ##pl = pleas_crash
       # print('Setting soil properties for {} (input={})'.format(soil_out.name, soil_in.name))
       # replace_namelist_value(namelist, 'gammasat', soil_out.gammasat)
       # replace_namelist_value(namelist, 'nvg',      soil_out.nvg)
       # replace_namelist_value(namelist, 'Lvg',      soil_out.lvg)
       # replace_namelist_value(namelist, 'alphavg',  soil_out.alphavg)
       # replace_namelist_value(namelist, 'phir',     soil_out.phir)
       # replace_namelist_value(namelist, 'phi',      soil_out.phi_sat)
       # replace_namelist_value(namelist, 'phiwp',    soil_out.phi_wp)
       # replace_namelist_value(namelist, 'phifc',    soil_out.phi_fc)

        # Read back namelist
        nl = Read_namelist('{0}/data/namoptions.{1:03d}'.format(src_dir,expnr))

        # Copy/move files to work directory
        date_prev = date - datetime.timedelta(days = 1) 
        workdir = '{0}/{1:04d}{2:02d}{3:02d}'.format(path_out, date.year, date.month, date.day)
        prev_workdir = '{0}/{1:04d}{2:02d}{3:02d}'.format(path_out, date_prev.year, date_prev.month, date_prev.day)
        if not os.path.exists(workdir):
            os.makedirs(workdir)

        # Create SLURM runscript
        print('Creating runscript')
        ntasks = nl['run']['nprocx']*nl['run']['nprocy']
        nnodes = int(np.ceil(ntasks/28))
        create_runscript ('DALES{0:03d}_{1}'.format(expnr, n), ntasks, nnodes, walltime=35, work_dir=workdir, expnr=expnr)

        # Copy/move files to work directory
        exp_str = '{0:03d}'.format(expnr)
        to_copy = ['namoptions.{}'.format(exp_str), 'rrtmg_lw.nc', 'rrtmg_sw.nc',
                   'prof.inp.{}'.format(exp_str), 'scalar.inp.{}'.format(exp_str)]
        to_move = ['backrad.inp.{}.nc'.format(exp_str), 'lscale.inp.{}'.format(exp_str),\
                   'ls_flux.inp.{}'.format(exp_str), 'ls_fluxsv.inp.{}'.format(exp_str),\
                   'nudge.inp.{}'.format(exp_str), 'run_DALES.sh']

        print('Copying/moving input files')
        for f in to_move:
            shutil.move(f, '{}/{}'.format(workdir, f))
        for f in to_copy:
            shutil.copy(src_dir+'/data/'+f, '{}/{}'.format(workdir, f))

        if start_is_warm:
            # Link base state and restart files from `prev_wdir` to the current working directory)
            print('Creating symlinks to restart files')

            hh = int(t_exp.total_seconds()/3600)
            mm = int(t_exp.total_seconds()-(hh*3600))

            # Link base state profile
            f_in  = '{0}/baseprof.inp.{1:03d}'.format(prev_workdir, expnr)
            f_out = '{0}/baseprof.inp.{1:03d}'.format(workdir, expnr)

            if not os.path.exists(f_out):
                os.symlink(f_in, f_out)

            # Link restart files
            for i in range(nl['run']['nprocx']):
                for j in range(nl['run']['nprocy']):
                    for ftype in ['d','s','l']:

                        f_in  = '{0}/init{1}{2:03d}h{3:02d}mx{4:03d}y{5:03d}.{6:03d}'\
                                    .format(prev_workdir, ftype, hh, mm, i, j, expnr)
                        f_out = '{0}/init{1}000h00mx{2:03d}y{3:03d}.{4:03d}'\
                                    .format(workdir, ftype, i, j, expnr)

                        if not os.path.exists(f_out):
                            os.symlink(f_in, f_out)

        # Submit task, accounting for job dependencies in case of warm start
        #if auto_submit:
        #    if start_is_warm:
        #        run_id = submit('run.PBS', workdir, dependency=prev_run_id)
        #    else:
        #        run_id = submit('run.PBS', workdir)

        # Create and submit post-processing task
        #create_postscript('P{0:03d}_{1}'.format(expnr, n), walltime=24, work_dir=workdir, expnr=expnr,
        #        itot=nl['domain']['itot'], jtot=nl['domain']['jtot'], ktot=nl['domain']['kmax'], 
        #        nprocx=nl['run']['nprocx'], nprocy=nl['run']['nprocy'])

        #shutil.move('post.PBS', '{}/post.PBS'.format(workdir))

        #if auto_submit:
        #    post_id = submit('post.PBS', workdir, dependency=run_id)

        # Advance time and store some settings
        date += dt_exp
        n += 1
        prev_workdir = workdir
        # prev_workdir_r = workdir

        if auto_submit:
            prev_run_id = run_id
