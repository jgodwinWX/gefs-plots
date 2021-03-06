#!/usr/bin/env bash

# user settings
GRIBDIR=/home/jgodwin/Documents/python/python/gefs-plots/grib
PYDIR=/home/jgodwin/Documents/python/python/gefs-plots

# clean out the old grib data
rm $GRIBDIR/*

# get current date and hour
MONTH=$(date -u +"%m")
DATE=$(date -u +"%d")
YEAR=$(date -u +"%Y")
HOUR=$(date -u +"%H")

if [ $HOUR -ge 6 ] && [ $HOUR -lt 12 ]
then
    RUN=00
elif [ $HOUR -ge 12 ] && [ $HOUR -lt 18 ]
then
    RUN=06
elif [ $HOUR -ge 18 ]
then
    RUN=12
elif [ $HOUR -ge 00 ] && [ $HOUR -lt 6 ]
then
    DATE=$(date -u -d'yesterday' +"%d")
    RUN=18
else
    echo "Invalid hour!"
fi

# loop through forecast hours
for i in {0..384..6}
    do
    # loop through each perturbation
    for j in {1..20}
        do
            # make sure the forecast hour is 2+ digits
            if [ $i -lt 100 ]
            then
                fcstHour="0${i}"
                fcstHour="${fcstHour: -2}"
            else
                fcstHour="00${i}"
                fcstHour="${fcstHour: -3}"
            fi
            # make sure the perturbation number is 2 digits
            pert="0${j}"
            pert="${pert: -2}"
            # download the grib files
            url="https://www.ftp.ncep.noaa.gov/data/nccf/com/gens/prod/gefs."$YEAR""$MONTH""$DATE"/"$RUN"/pgrb2/gep"$pert".t"$RUN"z.pgrb2f"$fcstHour""
            echo $url
            if [ $i -eq 0 ]
            then
                if [ $i -lt 10 ]
                then
                    fcstHour="00${i}"
                elif [ $i -lt 100 ] && [ $i -ge 10 ]
                then
                    fcstHour="0${i}"
                fi
                echo "running get_inv.pl"
                echo $GRIBDIR/grib_gefs_"$YEAR""$MONTH""$DATE"_"$RUN"_"$fcstHour"_"$pert"
                #perl $PYDIR/get_inv.pl "${url}.idx" | grep ":TMP:" | grep ":2 m above ground" | \
                perl $PYDIR/get_inv.pl "${url}.idx" | grep -E ":(TMP|RH)" | grep ":2 m above ground" | \
                perl $PYDIR/get_grib.pl "${url}" $GRIBDIR/grib_gefs_"$YEAR""$MONTH""$DATE"_"$RUN"_"$fcstHour"_"$pert"
                echo "foo"
            else
                if [ $i -lt 10 ]
                then
                    fcstHour="00${i}"
                elif [ $i -lt 100 ] && [ $i -ge 10 ]
                then
                    fcstHour="0${i}"
                fi
                echo "${url}.idx" | grep -E ":(TMAX|TMIN|APCP|CSNOW|CICEP|CFRZR|CRAIN)" | 
                perl $PYDIR/get_inv.pl "${url}.idx" | grep -E ":(TMAX|TMIN|TMP|APCP|CSNOW|CICEP|CFRZR|CRAIN|RH)" | grep -E ":2 m above ground|surface" | \
                perl $PYDIR/get_grib.pl "${url}" $GRIBDIR/grib_gefs_"$YEAR""$MONTH""$DATE"_"$RUN"_"$fcstHour"_"$pert"
            fi
        done   
    done

python $PYDIR/ensemblemeans.py >& $PYDIR/ensemblemeans.out
python $PYDIR/htmlbuilder.py >& $PYDIR/htmlbuilder.out
scp $PYDIR/*.png jgodwin@jasonsweathercenter.com:/var/www/html/gefs/.
