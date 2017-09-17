import calendar
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas

def utc_to_local(utc_dt,offset):
    return utc_dt + datetime.timedelta(hours=offset)

def plotter(dataset,namestr,savestr,season):
    plt.clf()

    fig = plt.figure()

    ax = fig.add_subplot(1,1,1)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))

    plt.plot(dataset)
    plt.grid()

    # x axis
    plt.xticks(rotation=90)
    plt.xlabel('Date/Time (Local)')
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %b-%d'))

    # y axis and title
    plt.ylabel('Temperature (degrees Fahrenheit)')
    if season == 'warm':
        plt.ylim([50,110])
    elif season == 'cold':
        plt.ylim([0,80])
    else:
        plt.ylim([0,110])
    plt.title('GEFS Ensemble Daily %s' % namestr)
    plt.savefig(savestr,bbox_inches='tight')

# open the csv files
max_temp_df = pandas.DataFrame.from_csv('/home/jgodwin/python/gefs/maxtemps.csv')
min_temp_df = pandas.DataFrame.from_csv('/home/jgodwin/python/gefs/mintemps.csv')
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

# plot forecasts
plotter(highs,'High Temperature','highs.png',season)
plotter(lows,'Low Temperature','lows.png',season)

##### vv THIS PART STILL UNDER CONSTRUCTION vv #######

# create the webpage
html_file = open('dfw.html','w')

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
