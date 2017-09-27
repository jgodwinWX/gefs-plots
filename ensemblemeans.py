import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas
import os
import pygrib
import time

def lonConvert(longitude):
    # -180 to 0 is between 180 and 360
    if longitude < 0:
        return 360.0 + longitude
    # 0 to 180 are the same
    else:
        return longitude

def validTimes(initdate,inithour):
    date = datetime.datetime.strptime(initdate,'%Y%m%d')
    # make sure the initial time is four digits
    if len(inithour) < 4:
        inithour = "0" + inithour
    runinit = date + datetime.timedelta(hours=float(inithour[0:2]))
    return [runinit + datetime.timedelta(hours=x) for x in range(0,385,6)]

def kelvinToFahrenheit(temperature):
    return temperature * (9.0 / 5.0) - 459.67

def mmToInches(precipitation):
    return precipitation * 0.0393701

# set target latitude and longitude
# DFW
mylat = 32.896944
mylon = -97.038056

# Lincoln, NE
#mylat = 40.810556
#mylon = -96.680278

# Baton Rouge, LA
#mylat = 30.45
#mylon = -91.14

# Laramie, WY
#mylat = 41.316667
#mylon = -105.583333

# McGee Creek SP, OK
#mylat = 34.33
#mylon = -95.861667

directory = '/home/jgodwin/python/gefs-plots/grib/'

max_temp = np.empty([20,65])
min_temp = np.empty([20,65])
precip = np.empty([20,65])

min_temp[:,:] = np.NAN
max_temp[:,:] = np.NAN
precip[:,:] = np.NAN

for filename in sorted(os.listdir(directory)):
    print filename
    pert = float(filename[-2:]) - 1.0
    hour = float(filename[-6:-3]) / 6.0

    # open the grib file
    grbs = pygrib.open(directory + filename)

    # check for missing/bad files
    if os.stat(directory + filename).st_size < 40000:
        max_temp[int(pert)][int(hour)] = float('nan')
        min_temp[int(pert)][int(hour)] = float('nan')
        precip[int(pert)][int(hour)] = float('nan')
        continue

    # get the temperature data (Kelvin) and precipitation (kg/m^2 = mm)
    if '_000_' in filename:
        max_temp_k = grbs.select(name='2 metre temperature')[0].values
        precip_mm = np.zeros(np.shape(max_temp_k))
        min_temp_k = max_temp_k
        lats,lons = grbs.select(name='2 metre temperature')[0].latlons()
    else:
        max_temp_k = grbs.select(name='Maximum temperature')[0].values
        min_temp_k = grbs.select(name='Minimum temperature')[0].values
        precip_mm = grbs.select(name='Total Precipitation')[0].values
        lats,lons = grbs.select(name='Maximum temperature')[0].latlons()

    # convert to Fahrenheit and inches because 'Murica
    max_temp_f = kelvinToFahrenheit(max_temp_k)
    min_temp_f = kelvinToFahrenheit(min_temp_k)
    precip_in = mmToInches(precip_mm)

    # get data at mylat and mylon
    grblat = np.where(lats==round(mylat))[0][0]
    mylon = lonConvert(round(mylon))
    grblon = np.where(lons==mylon)[1][0]
    # sanity check the values
    if max_temp_f[grblat,grblon] > 150.0 or max_temp_f[grblat,grblon] < -100.0:
        max_temp[int(pert)][int(hour)] = float('nan')
    else:
        max_temp[int(pert)][int(hour)] = max_temp_f[grblat,grblon]

    if min_temp_f[grblat,grblon] > 150.0 or min_temp_f[grblat,grblon] < -100.0:
        min_temp[int(pert)][int(hour)] = float('nan')
    else:
        min_temp[int(pert)][int(hour)] = min_temp_f[grblat,grblon]

    precip[int(pert)][int(hour)] = precip_in[grblat,grblon]

    grbs.close()

# compute ensemble mean at each forecast hour
max_ensmean = [0.0] * 65
min_ensmean = [0.0] * 65
precip_ensmean = [0.0] * 65
for i in range(0,65):
    max_ensmean[i] = np.nanmean(max_temp[:,i])
    min_ensmean[i] = np.nanmean(min_temp[:,i])
    precip_ensmean[i] = np.nanmean(precip[:,i])

# create ensemble mean plot
vtimes = validTimes(str(grbs.message(1).dataDate),str(grbs.message(1).dataTime))
plt.clf()
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
plt.plot(vtimes,max_ensmean,color='r',label='Max Temperature')
plt.plot(vtimes,min_ensmean,color='b',label='Min Temperature')
plt.grid()

# x axis settings
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)')
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))

# y axis and title
plt.ylabel('Temperature (degrees Fahrenheit)')
plt.title('GEFS Ensemble Mean 6-Hourly Temperature')
plt.legend(loc='upper right')
plt.savefig('ensmean_temp.png',bbox_inches='tight')

# write data out for each ensemble member
column_headers = [str('gep' + str(x)) for x in range(1,21)]
max_df = pandas.DataFrame(np.transpose(max_temp),index=vtimes,columns=column_headers)
max_df.index.name = 'ValidTime'
min_df = pandas.DataFrame(np.transpose(min_temp),index=vtimes,columns=column_headers)
min_df.index_name = 'ValidTime'
precip_df = pandas.DataFrame(np.transpose(precip),index=vtimes,columns=column_headers)
precip_df.index.name = 'ValidTime'

# create the precipitation mean plot
plt.clf()
fig = plt.figure()
ax = fig.add_subplot(1,1,1)
plt.bar(vtimes,precip_ensmean,width=0.25,color='g',align='center',label='6-Hour Precipitation')
plt.plot(vtimes,np.cumsum(precip_ensmean),color='b',label='Run-Accumulated Precipitation')
plt.grid()

# x axis settings
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)')
plt.xlim([np.min(vtimes),np.max(vtimes)])
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))

# y axis and title
plt.ylabel('Precipitation (inches)')
plt.title('GEFS Ensemble Mean Precipitation')
plt.legend(loc='upper left')
plt.savefig('ensmean_precip.png',bbox_inches='tight')

max_df.to_csv('/home/jgodwin/python/gefs-plots/maxtemps.csv')
min_df.to_csv('/home/jgodwin/python/gefs-plots/mintemps.csv')
precip_df.to_csv('/home/jgodwin/python/gefs-plots/precip.csv')
