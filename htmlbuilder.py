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

def plotter(dataset,namestr,savestr,season,inittime):
    plt.clf()

    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(1,1,1)

    plt.plot(dataset)
    plt.grid()

    # x axis
    plt.xlim([dataset.index[0],dataset.index[-1]])
    plt.xticks(dataset.index,rotation=90)
    plt.xlabel('Date/Time (UTC)',fontsize=14)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

    # y axis and title
    plt.ylabel('Temperature (degrees Fahrenheit)',fontsize=14)
    if season == 'warm':
        plt.ylim([40,110])
        plt.yticks(numpy.arange(40,110,5))
    elif season == 'cold':
        plt.ylim([0,90])
        plt.yticks(numpy.arange(0,90,5))
    elif season == 'dwpt':
        plt.ylim([20,85])
        plt.yticks(numpy.arange(20,85,5))
    else:
        plt.ylim([0,110])
        plt.yticks(numpy.arange(0,110,5))
    plt.title('GEFS Ensemble Daily %s (init: %s)' % (namestr,inittime),fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

def precip_plotter(dataset,namestr,savestr,inittime):
    plt.clf()

    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(1,1,1)

    plt.plot(numpy.cumsum(dataset))
    plt.grid()

    # x axis
    plt.xlim([dataset.index[0],dataset.index[-1]])
    plt.xticks(dataset.index,rotation=90)
    plt.xlabel('Date/Time (UTC)',fontsize=14)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

    # y axis and title
    plt.ylim([0.0,4.0])
    plt.yticks([0,0.1,0.25,0.50,1,2,3,4])
    plt.ylabel('Precipitation (inches)',fontsize=14)
    plt.title('GEFS Ensemble Daily %s (init: %s)' % (namestr,inittime),fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

def box_and_whisker(dataset,valid_dates,datatype,unitstr,namestr,savestr,inittime):
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
        plt.ylim([20,85])
        plt.yticks(numpy.arange(20,85,5))
    elif 'Precip' in namestr:
        plt.ylim([0.0,4.0])
        plt.yticks([0,0.10,0.25,0.50,1.0,2.0,3.0,4.0])

    # y axis and title
    plt.ylabel('%s (%s)' % (datatype,unitstr),fontsize=14)
    plt.title('GEFS Ensemble Daily %s (init: %s)' % (namestr,inittime),fontsize=16)
    plt.savefig(savestr,bbox_inches='tight')

# open the csv files
savedir = '/home/jgodwin/Documents/python/python/gefs-plots'
max_temp_df = pandas.read_csv('%s/maxtemps.csv' % savedir,index_col=0)
min_temp_df = pandas.read_csv('%s/mintemps.csv' % savedir,index_col=0)
dpt_df = pandas.read_csv('%s/dewpoint.csv' % savedir,index_col=0)
precip_df = pandas.read_csv('%s/precip.csv' % savedir,index_col=0)
locname = 'Dallas/Fort Worth, TX'
season = 'warm'
utcoffset = 0

# convert the valid times into local times
max_temp_df.index = pandas.to_datetime(max_temp_df.index)
min_temp_df.index = pandas.to_datetime(min_temp_df.index)
dpt_df.index = pandas.to_datetime(dpt_df.index)
precip_df.index = pandas.to_datetime(precip_df.index)
localtimes = [0.0] * len(max_temp_df.index)
dates = [0.0] * len(max_temp_df.index)
for ix,i in enumerate(max_temp_df.index):
    localtimes[ix] = utc_to_local(i,utcoffset)
    dates[ix] = datetime.datetime.strftime(i,'%m/%d/%Y')

highs = max_temp_df.groupby(lambda row: row.date()).max()
lows = min_temp_df.groupby(lambda row: row.date()).min()
dpts = dpt_df.groupby(lambda row: row.date()).mean()
precip = precip_df.groupby(lambda row: row.date()).sum()

valid_dates = [datetime.datetime.strptime(x,'%m/%d/%Y') for x in sorted(set(dates))]
inittime = datetime.datetime.strftime(max_temp_df.index[0],'%m/%d %H') + '00 UTC'

# truncate highs/lows since we are computing on closed intervals
if max_temp_df.index[0].hour == 0:
    lows = lows[0:-2]
    valid_dates_lo = valid_dates[0:-2]
    valid_dates_hi = valid_dates
elif max_temp_df.index[0].hour == 12:
    highs = highs[0:-2]
    valid_dates_hi = valid_dates[0:-2]
    valid_dates_lo = valid_dates

# plot forecasts
plotter(highs,'High Temperature at %s' % locname,'%s/highs.png' % savedir,season,inittime)
plotter(lows,'Low Temperature at %s' % locname,'%s/lows.png' % savedir,season,inittime)
plotter(dpts,'Mean Daily Dewpoint at %s' % locname,'%s/dwpt.png' % savedir,'dwpt',inittime)
precip_plotter(precip,'Run-Total Precip. at %s' % locname,'%s/precip.png' % savedir,inittime)

# get number of members containing precipitation
precip_members = numpy.zeros(17)
for i in range(numpy.shape(precip)[0]):
    precip_members[i] = numpy.shape((numpy.where(numpy.array(precip)[i,:]>0)))[1] / 20.0

# create number of members plot
plt.clf()
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(1,1,1)

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
plt.xlim(valid_dates[0],valid_dates[-1])
plt.xlabel('Date/Time (UTC)',fontsize=14)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

# y axis and title
plt.ylabel('Percent of Members',fontsize=14)
plt.ylim([0,1])
plt.yticks(numpy.arange(0,1,0.1))
vals = ax.get_yticks()
ax.set_yticklabels(['{:.0f}%'.format(x*100) for x in vals])
plt.title('GEFS Members Indicating Precipitation at %s (init: %s)' % (locname,inittime),fontsize=16)
plt.savefig('precip_percent.png',bbox_inches='tight')

# create box and whisker plots
box_and_whisker(highs,valid_dates_hi,'Temperature','degrees Fahrenheit','High Temperature at %s' % locname,'%s/box_highs.png' % savedir,inittime)
box_and_whisker(lows,valid_dates_lo,'Temperature','degrees Fahrenheit','Low Temperature at %s' % locname,'%s/box_lows.png' % savedir,inittime)
box_and_whisker(dpts,valid_dates,'Dewpoint','degrees Fahrenheit','Mean Dewpoint at %s' % locname,'%s/box_dwpt.png' % savedir,inittime)
box_and_whisker(precip,valid_dates,'Precipitation','inches','Total Precip. at %s' % locname,'%s/box_precip.png' % savedir,inittime)

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
