#!%SHELL:/bin/ksh%  
set -e          # stop the shell on first error
set -u          # fail when using an undefined variable
set -x          # echo script lines as they are executed
set -o pipefail # fail if last(rightmost) command exits with a non-zero status
 
# Defines the variables that are needed for any communication with ECF
export ECF_PORT=16889    # The server port number
export ECF_HOST=login4.bullx    # The host name where the server is running
export ECF_NAME=%ECF_NAME%    # The name of this current task
export ECF_PASS=%ECF_PASS%    # A unique password, used for job validation & zombie detection
export ECF_TRYNO=%ECF_TRYNO%  # Current try number of the task
export ECF_RID=$$             # record the process id. Also used for zombie detection
# export NO_ECF=1             # uncomment to run as a standalone task on the command line

export MAIL_ON_ABORT=natalie.theeuwes@knmi.nl

# Define the path where to find ecflow_client
# make sure client and server use the *same* version.
# Important when there are multiple versions of ecFlow
export PATH=/usr/local/apps/ecflow/%ECF_VERSION%/bin:$PATH
 
# Tell ecFlow we have started
ecflow_client --init=$$
 
 
# Define a error handler
ERROR() {
   set +e                      # Clear -e flag, so we don't fail
                               # Syncing logs between cca/ccb  and ecgb
      cat << \EndOnERR
ERROR:ECF_ABORT_HM
</PRE>
<PRE>
EndOnERR
   # Send e-mail if address set in ecf/config_exp.h
   if [ -n "$MAIL_ON_ABORT" ]; then
      suite_state=$(ecflow_client --get_state=/$EXP 2>&1 | grep "^suite $EXP")
      if echo $suite_state | grep -qv 'state:aborted'; then  # only send mail if server isn't already in aborted state
         if [ %ECF_TRYNO% -ge %ECF_TRIES% ]; then            # and we tried the maximum number of times
            mymailx="${MAILX-mailx -n}"
            subject="[WINS50 ABORT] in $EXP for task $TASK"
            errmsg="Task $TASK of $EXP became aborted at $(date +'%%Y-%%m-%%d %%H:%%M:%%S') (try %ECF_TRYNO% of %ECF_TRIES%)"
            showlog=""
            attachlog=""
            if [ -f %ECF_JOBOUT% ]; then
               errmsg="$errmsg\n\n---- Last 200 lines of %ECF_JOBOUT% ----\n\n"
               showlog="tail -n 200 %ECF_JOBOUT%"
               attachlog="-a %ECF_JOBOUT%"
            fi

            # send mail from ECF_HOST
            if [ $(hostname) = $ECF_HOST ]; then
               (printf "$errmsg\n"; $showlog) | $mymailx -s "$subject" $attachlog $MAIL_ON_ABORT
               ierr=$?
            else
               ssh $ECF_HOST /bin/sh <<EndOfMail
                  (printf "$errmsg\n"; $showlog) | $mymailx -s "$subject" $attachlog $MAIL_ON_ABORT
EndOfMail
               ierr=$?
            fi
            if [ $ierr -ne 0 ]; then
               echo "Sending mail failed:"
               echo "mailx  : $mymailx"
               echo "To     : $MAIL_ON_ABORT"
               echo "Subject: $subject"
            fi
         fi
      fi
   fi

   ecflow_client --abort=trap  # Notify ecFlow that something went wrong, using 'trap' as the reason
   trap 0                      # Remove the trap
   exit 1                      # End the script with exit code 1
}
 
 
# Trap any calls to exit and errors caught by the -e flag
trap ERROR 0
 
 
# Trap any signal that may cause the script to fail
trap '{ echo "Killed by a signal"; ERROR ; }' 1 2 3 4 5 6 7 8 10 12 13 15
