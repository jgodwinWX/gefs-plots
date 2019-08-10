#!/usr/bin/env python
''' Ingests GEFS GRIB data and stores high and low temperature data, precipitation data, and
    dewpoint data for a user-specified location. Creates some plots of 6-hourly forecast
    information, then writes out CSV files containing high/low temperature, precipitation,
    and dewpoint data for each ensemble member for use in htmlbuilder.py.
'''

import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas
import os
import pygrib
import time

__author__ = 'Jason Godwin'
__license__ = 'GPL'
__maintainer__ = 'Jason Godwin'
__email__ = 'jasonwgodwin@gmail.com'
__status__ = 'Production'

# converts the user input longitude to the coordinate system used in the GRIB files
def lonConvert(longitude):
    # -180 to 0 is between 180 and 360
    if longitude < 0:
        return 360.0 + longitude
    # 0 to 180 are the same
    else:
        return longitude

# gets the correct valid times for each GRIB file
def validTimes(initdate,inithour):
    date = datetime.datetime.strptime(initdate,'%Y%m%d')
    # make sure the initial time is four digits
    if len(inithour) < 4:
        inithour = "0" + inithour
    runinit = date + datetime.timedelta(hours=float(inithour[0:2]))
    return [runinit + datetime.timedelta(hours=x) for x in range(0,385,6)]

# convert temperature in Kelvin to degrees Fahrenheit
def kelvinToFahrenheit(temperature):
    return temperature * (9.0 / 5.0) - 459.67

# convert temperature in Kelvin to degrees Celsius
def kelvinToCelsius(temperature):
    return temperature - 272.15

# convert temperature in degrees Celsius to degrees Fahrenheit
def celsiusToFahrenheit(temperature):
    return 1.8 * temperature + 32.0

# computes dewpoint from relative humidity and temperature
def dewpointCalc(rh,tmp):
    # first we have to get the saturation vapor pressure from the temperature
    es = 6.11 * 10**((7.5 * tmp)/(237.3+tmp))
    return (237.3 * np.log((es*rh)/611)) / (7.5 * np.log(10) - np.log((es*rh)/611))

# convert millimeters of rainfall to inches of rainfall
def mmToInches(precipitation):
    return precipitation * 0.0393701

### USER SETTINGS BLOCK ###
savedir = '/home/jgodwin/Documents/python/python/gefs-plots'            # directory to save output
directory = '/home/jgodwin/Documents/python/python/gefs-plots/grib/'    # location of GRIB files
mylat = 32.896944                   # latitude (decimal degrees, negative for southern hemisphere)
mylon = -97.038056                  # longitude (decimal degrees, negative for western hemisphere)
locname = 'Dallas/Fort Worth, TX'   # name for location
testmode = False                    # set to True to run for the first 24 hours only
### END OF USER SETTINGS BLOCK ###

# create empty arrays (20 perturbations, 65 valid times)
max_temp = np.empty([20,65])    # maximum temperature
min_temp = np.empty([20,65])    # minimum temperature
dpt = np.empty([20,65])         # dewpoint
precip = np.empty([20,65])      # precipitation amount
snow = np.empty([20,65])        # categorical snow flag
sleet = np.empty([20,65])       # categorical sleet flag
fzra = np.empty([20,65])        # categorical freezing rain flag
rain = np.empty([20,65])        # categorical liquid rain flag

# default everything to NAN
min_temp[:,:] = np.NAN
max_temp[:,:] = np.NAN
dpt[:,:] = np.NAN
precip[:,:] = np.NAN
snow[:,:] = np.NAN
sleet[:,:] = np.NAN
fzra[:,:] = np.NAN
rain[:,:] = np.NAN

# loop through each GRIB file
for ix,filename in enumerate(sorted(os.listdir(directory))):
    print(filename)
    # get the perturbation and valid hour from the filename
    pert = float(filename[-2:]) - 1.0
    hour = float(filename[-6:-3]) / 6.0

    # open the grib file
    grbs = pygrib.open(directory + filename)

    # check for missing/bad files
    if os.stat(directory + filename).st_size < 40000:
        max_temp[int(pert)][int(hour)] = float('nan')
        min_temp[int(pert)][int(hour)] = float('nan')
        dpt[int(pert)][int(hour)] = float('nan')
        precip[int(pert)][int(hour)] = float('nan')
        snow[int(pert)][int(hour)] = float('nan')
        sleet[int(pert)][int(hour)] = float('nan')
        fzra[int(pert)][int(hour)] = float('nan')
        rain[int(pert)][int(hour)] = float('nan')
        continue

    # get the data
    if '_000_' in filename:
        # temperature data (K) - same as temperature for initial time
        max_temp_k = grbs.select(name='2 metre temperature')[0].values
        min_temp_k = max_temp_k
        temp_k = max_temp_k
        # relative humidity (%)
        relh_pct = grbs.select(name='2 metre relative humidity')[0].values
        # precipitation (mm) - zero for initial time
        precip_mm = np.zeros(np.shape(max_temp_k))
        # categorical precipitation flags
        catsnow = np.zeros(np.shape(max_temp_k))
        catsleet = np.zeros(np.shape(max_temp_k))
        catfzra = np.zeros(np.shape(max_temp_k))
        catrain = np.zeros(np.shape(max_temp_k))
        # latitude and longitude
        lats,lons = grbs.select(name='2 metre temperature')[0].latlons()
    else:
        # temperature data (K)
        max_temp_k = grbs.select(name='Maximum temperature')[0].values
        min_temp_k = grbs.select(name='Minimum temperature')[0].values
        temp_k = grbs.select(name='2 metre temperature')[0].values
        # relative humidity (%)
        relh_pct = grbs.select(name='2 metre relative humidity')[0].values
        # precipitation (mm)
        precip_mm = grbs.select(name='Total Precipitation')[0].values
        # categorical precipitation flags
        catsnow = grbs.select(name='Categorical snow')[0].values
        catsleet = grbs.select(name='Categorical ice pellets')[0].values
        catfzra = grbs.select(name='Categorical freezing rain')[0].values
        catrain = grbs.select(name='Categorical rain')[0].values
        # latitude and longitude
        lats,lons = grbs.select(name='Maximum temperature')[0].latlons()

    # convert to American units
    max_temp_f = kelvinToFahrenheit(max_temp_k)
    min_temp_f = kelvinToFahrenheit(min_temp_k)
    precip_in = mmToInches(precip_mm)

    # convert temperature to Celsius for use in the dewpoint formula
    temp_c = kelvinToCelsius(temp_k)

    # compute dewpoint from temperature and relative humidity then convert to Fahrenheit
    dpt_c = dewpointCalc(relh_pct,temp_c)
    dpt_f = celsiusToFahrenheit(dpt_c)

    # get data at mylat and mylon - round because we're on a 1deg x 1deg grid
    grblat = np.where(lats==round(mylat))[0][0]
    mylon = lonConvert(round(mylon))
    grblon = np.where(lons==mylon)[1][0]
    # sanity check the values
    # QC temperature
    if max_temp_f[grblat,grblon] > 150.0 or max_temp_f[grblat,grblon] < -100.0:
        max_temp[int(pert)][int(hour)] = float('nan')
    else:
        max_temp[int(pert)][int(hour)] = max_temp_f[grblat,grblon]

    if min_temp_f[grblat,grblon] > 150.0 or min_temp_f[grblat,grblon] < -100.0:
        min_temp[int(pert)][int(hour)] = float('nan')
    else:
        min_temp[int(pert)][int(hour)] = min_temp_f[grblat,grblon]

    # QC dewpoint
    if dpt_f[grblat,grblon] > 100.0 or dpt_f[grblat,grblon] < -50.0:
        dpt[int(pert)][int(hour)] = float('nan')
    else:
        dpt[int(pert)][int(hour)] = dpt_f[grblat,grblon]

    # set everything else
    precip[int(pert)][int(hour)] = precip_in[grblat,grblon]
    snow[int(pert)][int(hour)] = catsnow[grblat,grblon]
    sleet[int(pert)][int(hour)] = catsleet[grblat,grblon]
    fzra[int(pert)][int(hour)] = catfzra[grblat,grblon]
    rain[int(pert)][int(hour)] = catrain[grblat,grblon]
    
    # kill switch for test mode
    if testmode and ix >= 20 * 4:
        break

# compute ensemble mean at each forecast hour
# initialize everything to zero
max_ensmean = [0.0] * 65
min_ensmean = [0.0] * 65
dpt_ensmean = [0.0] * 65
precip_ensmean = [0.0] * 65
snowmems = np.array([0.0] * 65)
sleetmems = np.array([0.0] * 65)
fzramems = np.array([0.0] * 65)
rainmems = np.array([0.0] * 65)
# actual ensemble mean calculations
for i in range(0,65):
    max_ensmean[i] = np.nanmean(max_temp[:,i])
    min_ensmean[i] = np.nanmean(min_temp[:,i])
    dpt_ensmean[i] = np.nanmean(dpt[:,i])
    precip_ensmean[i] = np.nanmean(precip[:,i])
    snowmems[i] = np.sum(snow[:,i]) / 20.0
    sleetmems[i] = np.sum(sleet[:,i]) / 20.0
    fzramems[i] = np.sum(fzra[:,i]) / 20.0
    rainmems[i] = np.sum(rain[:,i]) / 20.0

# valid/initial time information
vtimes = validTimes(str(grbs.message(1).dataDate),str(grbs.message(1).dataTime))
inittime = datetime.datetime.strftime(vtimes[0],'%m/%d %H') + '00 UTC'

### ENSEMBLE MEAN PLOTS ###
# TEMPERATURE
plt.clf()
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(1,1,1)
plt.plot(vtimes,max_ensmean,color='r',label='Max Temperature')
plt.plot(vtimes,min_ensmean,color='b',label='Min Temperature')
plt.grid(which='major',linestyle='-',color='black')
plt.grid(which='minor',linestyle='--',color='gray')

# x axis settings
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)',fontsize=14)
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))

# y axis and title
plt.yticks(np.arange(0,110,5))
plt.ylim([0,110])
plt.ylabel('Temperature (degrees Fahrenheit)',fontsize=14)
plt.title('GEFS Ensemble Mean 6-Hourly Temperature for %s (init: %s)' % (locname,inittime),\
    fontsize=16)
plt.legend(loc='upper right',fontsize=12)
plt.savefig('%s/ensmean_temp.png' % savedir,bbox_inches='tight')
plt.close(fig)

# PRECIPITATION
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(1,1,1)
plt.bar(vtimes,precip_ensmean,width=0.25,color='g',align='center',label='6-Hour Precipitation')
plt.plot(vtimes,np.cumsum(precip_ensmean),color='b',label='Run-Accumulated Precipitation')
plt.grid(which='major',linestyle='-',color='black')
plt.grid(which='minor',linestyle='--',color='gray')

# x axis settings
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)',fontsize=14)
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))

# y axis and title
plt.yticks([0,0.1,0.25,0.50,1,2,3,4])
plt.ylim([0,4])
plt.ylabel('Precipitation (inches)',fontsize=14)
plt.title('GEFS Ensemble Mean Precipitation for %s (init: %s)' % (locname,inittime),fontsize=16)
plt.legend(loc='upper left',fontsize=12)
plt.savefig('%s/ensmean_precip.png' % savedir,bbox_inches='tight')
plt.close(fig)

### DEWPOINT ###
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(1,1,1)
plt.plot(vtimes,dpt_ensmean,color='g',label='Dewpoint')
plt.grid(which='major',linestyle='-',color='black')
plt.grid(which='minor',linestyle='--',color='gray')

# x axis settings
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)',fontsize=14)
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))

# y axis and title
plt.ylim([20,85])
plt.yticks(np.arange(20,85,5))
plt.ylabel('Dewpoint Temperature (F)',fontsize=14)
plt.title('GEFS Ensemble Mean 6-Hourly Dewpoint for %s (init: %s)' % (locname,inittime),fontsize=16)
plt.legend(loc='upper right',fontsize=12)
plt.savefig('%s/ensmean_dwpt.png' % savedir,bbox_inches='tight')
plt.close(fig)

# CATEGORICAL PRECIPITATION TYPE
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(1,1,1)
plt.bar(vtimes,snowmems,width=0.25,color='b',label='Snow',align='center')
plt.bar(vtimes,sleetmems,width=0.25,color='y',label='Sleet',align='center',bottom=snowmems)
plt.bar(vtimes,fzramems,width=0.25,color='r',label='Freezing Rain',align='center',\
    bottom=snowmems+sleetmems)
plt.bar(vtimes,rainmems,width=0.25,color='g',label='Liquid Rain',align='center',\
    bottom=snowmems+sleetmems+fzramems)

# grid
plt.grid(which='major',linestyle='-',color='black')
plt.grid(which='minor',linestyle='--',color='gray')

# x axis
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)',fontsize=14)
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))

# y axis and title
plt.ylim([0,1])
plt.yticks(np.arange(0,1,0.1))
plt.ylabel('Percent of Members',fontsize=14)
vals = ax.get_yticks()
ax.set_yticklabels(['{:.0f}%'.format(x*100) for x in vals])

plt.title('GEFS Categorical Precipitation Type for %s (init: %s)' % (locname,inittime),fontsize=16)
plt.legend(loc='upper right',fontsize='12')
plt.savefig('%s/ptype.png' % savedir,bbox_inches='tight')
plt.close(fig)

# write data out for each ensemble member
column_headers = [str('gep' + str(x)) for x in range(1,21)]
max_df = pandas.DataFrame(np.transpose(max_temp),index=vtimes,columns=column_headers)
max_df.index.name = 'ValidTime'
min_df = pandas.DataFrame(np.transpose(min_temp),index=vtimes,columns=column_headers)
min_df.index_name = 'ValidTime'
precip_df = pandas.DataFrame(np.transpose(precip),index=vtimes,columns=column_headers)
precip_df.index.name = 'ValidTime'
dpt_df = pandas.DataFrame(np.transpose(dpt),index=vtimes,columns=column_headers)
dpt_df.index.name = 'ValidTime'

# write ensemble member information to CSV files
max_df.to_csv('%s/maxtemps.csv' % savedir)
min_df.to_csv('%s/mintemps.csv' % savedir)
precip_df.to_csv('%s/precip.csv' % savedir)
dpt_df.to_csv('%s/dewpoint.csv' % savedir)
