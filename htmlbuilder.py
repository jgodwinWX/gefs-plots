import calendar
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy
import pandas

def utc_to_local(utc_dt,offset):
    return utc_dt + datetime.timedelta(hours=offset)

def plotter(dataset,namestr,savestr,season):
    plt.clf()

    fig = plt.figure(figsize=(12,8))

    ax = fig.add_subplot(1,1,1)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))

    plt.plot(dataset)
    plt.grid()

    # x axis
    plt.xticks(rotation=90)
    plt.xlabel('Date/Time (Local)',fontsize=14)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

    # y axis and title
    plt.ylabel('Temperature (degrees Fahrenheit)',fontsize=14)
    if season == 'warm':
        plt.ylim([40,110])
    elif season == 'cold':
        plt.ylim([0,90])
    elif season == 'dwpt':
        plt.ylim([0,100])
    else:
        plt.ylim([0,110])
    plt.title('GEFS Ensemble Daily %s' % namestr,fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

def precip_plotter(dataset,namestr,savestr):
    plt.clf()

    fig = plt.figure(figsize=(12,8))

    ax = fig.add_subplot(1,1,1)

    plt.plot(numpy.cumsum(dataset))
    plt.grid()

    # x axis
    plt.xticks(rotation=90)
    plt.xlabel('Date/Time (Local)',fontsize=14)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

    # y axis and title
    plt.ylabel('Precipitation (inches)',fontsize=14)
    plt.title('GEFS Ensemble Daily %s' % namestr,fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

def box_and_whisker(dataset,valid_dates,datatype,unitstr,namestr,savestr):
    plt.clf()

    fig = plt.figure(figsize=(12,8))

    ax = fig.add_subplot(1,1,1)

    # reformat the date labels
    valid_dates = [datetime.datetime.strftime(x,'%a %b-%d') for x in sorted(valid_dates)]

    plt.boxplot(numpy.transpose(numpy.array(dataset)),whis='range',labels=valid_dates)
    plt.grid()

    # x axis
    plt.xticks(rotation=90)
    plt.xlabel('Date')

    # set the y limits for temperatures
    if 'Temperature' in namestr:
        plt.ylim([0,110])
        plt.yticks(numpy.arange(0,110,5))
    elif 'Dewpoint' in namestr:
        plt.ylim([0,100])
        plt.yticks(numpy.arange(0,100,5))

    # y axis and title
    plt.ylabel('%s (%s)' % (datatype,unitstr),fontsize=14)
    plt.title('GEFS Ensemble Daily %s' % namestr,fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

# open the csv files
savedir = '/home/jgodwin/Documents/python/python/gefs-plots'
max_temp_df = pandas.DataFrame.from_csv('%s/maxtemps.csv' % savedir)
min_temp_df = pandas.DataFrame.from_csv('%s/mintemps.csv' % savedir)
dpt_df = pandas.DataFrame.from_csv('%s/dewpoint.csv' % savedir)
precip_df = pandas.DataFrame.from_csv('%s/precip.csv' % savedir)
season = 'warm'

# convert the valid times into local times
max_temp_df.index = pandas.to_datetime(max_temp_df.index)
localtimes = [0.0] * len(max_temp_df.index)
dates = [0.0] * len(max_temp_df.index)
for ix,i in enumerate(max_temp_df.index):
    localtimes[ix] = utc_to_local(i,-6)
    dates[ix] = datetime.datetime.strftime(i,'%m/%d/%Y')

highs = max_temp_df.groupby(lambda row: row.date()).max()
lows = min_temp_df.groupby(lambda row: row.date()).min()
dpts = dpt_df.groupby(lambda row: row.date()).mean()
precip = precip_df.groupby(lambda row: row.date()).sum()

# plot forecasts
plotter(highs,'High Temperature','%s/highs.png' % savedir,season)
plotter(lows,'Low Temperature','%s/lows.png' % savedir,season)
plotter(dpts,'Mean Daily Dewpoint','%s/dwpt.png' % savedir,'dwpt')
precip_plotter(precip,'Run-Accumulated Precipitation','%s/precip.png' % savedir)

# get number of members containing precipitation
precip_members = numpy.zeros(17)
for i in range(numpy.shape(precip)[0]):
    precip_members[i] = numpy.shape((numpy.where(numpy.array(precip)[i,:]>0)))[1] / 20.0

# create number of members plot
plt.clf()

fig = plt.figure(figsize=(12,8))

ax = fig.add_subplot(1,1,1)

valid_dates = [datetime.datetime.strptime(x,'%m/%d/%Y') for x in sorted(set(dates))]

plt.bar(valid_dates,precip_members,width=0.5,align='center')
plt.grid()

# add ensmble mean values to top of bars
rects = ax.patches
labels = ['%.02f' % x for x in numpy.nanmean(numpy.array(precip),axis=1)]
for rect,label in zip(rects,labels):
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2, height + 0.01, label, ha='center', va='bottom',fontsize=12)

# x axis
plt.xticks(rotation=90)
plt.xlabel('Date/Time (Local)',fontsize=14)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

# y axis and title
plt.ylabel('Percent of Members',fontsize=14)
plt.ylim([0,1])
vals = ax.get_yticks()
ax.set_yticklabels(['{:.0f}%'.format(x*100) for x in vals])
plt.title('GEFS Members Indicating Precipitation',fontsize=16)
plt.savefig('precip_percent.png',bbox_inches='tight')

# create box and whisker plots
box_and_whisker(highs,valid_dates,'Temperature','degrees Fahrenheit','High Temperature','%s/box_highs.png' % savedir)
box_and_whisker(lows,valid_dates,'Temperature','degrees Fahrenheit','Low Temperature','%s/box_lows.png' % savedir)
box_and_whisker(dpts,valid_dates,'Dewpoint','degrees Fahrenheit','Mean Dewpoint','%s/box_dwpt.png' % savedir)
box_and_whisker(precip,valid_dates,'Precipitation','inches','Accumulated Precipitation','%s/box_precip.png' % savedir)

##### vv THIS PART STILL UNDER CONSTRUCTION vv #######

# create the webpage
html_file = open('%s/dfw.html' % savedir,'w')

# page header
html_info = """ 
    <html>
    <head>
        <title>GEFS Viewer</title>
    </head>
    <body>
        <h1>GEFS Temperature Plot for DFW</h1>
        <h2>Initialized: %s UTC</h2>
    """ % datetime.datetime.strftime(max_temp_df.index[0],'%m/%d/%Y %H:%M')

# create table header
html_info += ''' 
    <table border=1 cols=22 width=1200px>
        <tr><th>Valid Time</th>
'''

# create columns for each ensemble member
for i in range(1,21):
    html_info += ''' 
        <th>GEP %d</th>
    ''' % i 

html_info += '<th>Ensemble Mean</th></tr>'

html_file.write(html_info)
html_file.close()
