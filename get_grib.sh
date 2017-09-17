#!/usr/bin/env bash

# user settings
GRIBDIR=/home/jgodwin/python/gefs/grib

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
            url="http://www.ftp.ncep.noaa.gov/data/nccf/com/gens/prod/gefs."$YEAR""$MONTH""$DATE"/"$RUN"/pgrb2/gep"$pert".t"$RUN"z.pgrb2f"$fcstHour""
            echo $url
            if [ $i -eq 0 ]
            then
                echo "running get_inv.pl"
                perl get_inv.pl "${url}.idx" | grep ":TMP:" | grep ":2 m above ground" | \
                perl get_grib.pl "${url}" $GRIBDIR/grib_gefs_"$YEAR""$MONTH""$DATE"_"$RUN"_"$pert"_"$fcstHour"
            else
                #perl get_inv.pl "${url}.idx" | grep ":TMAX:" \
                perl get_inv.pl "${url}.idx" | grep -E ":(TMAX|TMIN):2 m above ground" | \
                perl get_grib.pl "${url}" $GRIBDIR/grib_gefs_"$YEAR""$MONTH""$DATE"_"$RUN"_"$pert"_"$fcstHour"
            fi
        done   
    done
