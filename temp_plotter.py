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

# set target latitude and longitude
mylat = 32.896944
mylon = -97.038056
directory = '/home/jgodwin/python/gefs-plots/grib/'

max_temp = np.empty([20,65])
min_temp = np.empty([20,65])

min_temp[:,:] = np.NAN
max_temp[:,:] = np.NAN

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
        continue

    # get the temperature data (Kelvin)
    if '_000_' in filename:
        max_temp_k = grbs.select(name='2 metre temperature')[0].values
        min_temp_k = max_temp_k
        lats,lons = grbs.select(name='2 metre temperature')[0].latlons()
    else:
        max_temp_k = grbs.select(name='Maximum temperature')[0].values
        min_temp_k = grbs.select(name='Minimum temperature')[0].values
        lats,lons = grbs.select(name='Maximum temperature')[0].latlons()

    # convert to Fahrenheit because 'Murica
    max_temp_f = kelvinToFahrenheit(max_temp_k)
    min_temp_f = kelvinToFahrenheit(min_temp_k)

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

# compute ensemble mean at each forecast hour
max_ensmean = [0.0] * 65
min_ensmean = [0.0] * 65
for i in range(0,65):
    max_ensmean[i] = np.nanmean(max_temp[:,i])
    min_ensmean[i] = np.nanmean(min_temp[:,i])

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
ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))

# y axis and title
plt.ylabel('Temperature (degrees Fahrenheit)')
plt.title('GEFS Ensemble Mean 6-Hourly Temperature')
plt.legend(loc='lower center')
plt.savefig('ensmean.png',bbox_inches='tight')

# write data out for each ensemble member
column_headers = [str('gep' + str(x)) for x in range(1,21)]
max_df = pandas.DataFrame(np.transpose(max_temp),index=vtimes,columns=column_headers)
max_df.index.name = 'ValidTime'
min_df = pandas.DataFrame(np.transpose(min_temp),index=vtimes,columns=column_headers)
min_df.index_name = 'ValidTime'

max_df.to_csv('/home/jgodwin/python/gefs-plots/maxtemps.csv')
min_df.to_csv('/home/jgodwin/python/gefs-plots/mintemps.csv')
