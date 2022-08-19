date=$1
exp=$2
dir="/nfs/home/users/theeuwes/work/DALES_runs/$date/"
cwd="/nfs/home/users/theeuwes/work/DALES_runs/ecf/scr/"

cp $cwd/mergecross.py $dir

# combine crossections
#    cape
type="cape"

for vars in "lwp" "twp" "surfprec"
do
        echo $dir/mergecross.py $vars $exp
        python3 $dir/mergecross.py $dir $type $vars $exp
        mv $dir$type.$vars.$exp.nc $dir$type.$vars.$date.$exp.nc
done

#type="surfcross"
#for vars in "H" "LE" "G0" "tskin" "obuk" "ustar" "cliq"
#do
#        echo Merging $type var $vars
#        python3 $dir/mergecross.py $dir $type $vars $exp
#        mv $dir$type.$vars.$exp.nc $dir$type.$vars.$date.$exp.nc
#done

type="crossxy.0002"
for vars in "ql" "qt" "thl" "u" "v" "w" "thv" "e120"
do
        echo Merging $type var $vars
        python3 $dir/mergecross.py $dir $type $vars $exp
        mv $dir$type.$vars.$exp.nc $dir$type.$vars.$date.$exp.nc
done

type="crossxz"
for vars in "ql" "qt" "thl" "u" "v" "w" "thv" "e120"
do
        echo Merging $type var $vars
        python3 $dir/mergecross.py $dir $type $vars $exp
        mv $dir$type.$vars.$exp.nc $dir$type.$vars.$date.$exp.nc
done

type="crossyz"
for vars in "ql" "qt" "thl" "u" "v" "w" "thv" "e120"
do
        echo Merging $type var $vars
        python3 $dir/mergecross.py $dir $type $vars $exp
        mv $dir$type.$vars.$exp.nc $dir$type.$vars.$date.$exp.nc
done

