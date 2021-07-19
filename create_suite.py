#!/usr/bin/env python 
import os
import ecflow
from datetime import date,timedelta

yesterday = date.today()-timedelta(days=1)    
print("Creating suite  definition")      
home = os.path.join(os.getenv("HOME"),"work/DALES_runs/ecf")
defs = ecflow.Defs()

suite = defs.add_suite("DALES")
suite.add_variable("ECF_HOME",home)
suite.add_repeat( ecflow.RepeatDate("DATE",20210627,20250101,1) )

## pre-process family ##
prep = suite.add_family("prepare")
##prep.add_time("08:00") --> need to catch up so removing starting time
soil = prep.add_task("get_soil_IFS")
prep.add_task("get_HARM_forcing")
inp = prep.add_task("create_input_DALES")
inp.add_trigger("get_soil_IFS == complete and get_HARM_forcing == complete")

## run family ##
fam = suite.add_family("run")
run = fam.add_task("run_DALES")
run.add_trigger("../prepare == complete")

## run family ##
post = suite.add_family("postprocessing")
merge = post.add_task("merge_crosssections")
merge.add_variable("EXP",'001')
merge.add_trigger("../run == complete")
store = post.add_task("store_somewhere")
store.add_variable("EXP",001)
store.add_trigger("merge_crosssections == complete")

print(defs)

print("Checking job creation: .ecf -> .job0") 
print(defs.check_job_creation())
print("Saving definition to file 'run.def'")
defs.save_as_defs("run.def")

