"""
import ecflow
try:
    print("Loading definition in 'test.def' into the server")
    ci = ecflow.Client() 
    ci.set_host_port("login4.bullx","16889") 
    ci.load("run.def")      # read definition from disk and load into the server
except RuntimeError as e:
    print("Failed:",   e)

"""

import ecflow
  
try:
    ci = ecflow.Client()
    ci.set_host_port("login4.bullx","16889") 
    ci.sync_local()      # get the defs from the server, and place on ci
    defs = ci.get_defs() # retrieve the defs from ci
    print(defs)
    #if len(defs) == 0:    
    #    print("No suites in server, loading defs from disk")
    #ci.load("run.def")
    #      
    #    print("Restarting the server. This starts job scheduling")
    #    ci.restart_server()
    #else:
    #    print("read definition from disk and replace on the server")
    ci.replace("/DALES", "run.def")
  
    print("Begin the suite named 'DALES'")
    ci.begin_suite("DALES")
  
except RuntimeError as e:
    print("Failed:",    e)
