# gefs-plots

This repo creates various plots of GEFS ensemble data.

Key Python packages:
-matplotlib
-numpy
-pandas
-pygrib

(Others are required, but these are probably the ones you don't have on a clean Linux
install...just install whatever the error messages tell you you're missing, but you
should not need anything too exotic).

### A WORD ON DIRECTORY PATHS ###
Before we delve into the details, note that you will need to change the directory paths
in ensemblemeans.py (right after the lat/long settings), the GRIBDIR environment variable
in get_grib.sh, and in htmlbuilder.py right after all the functions. My working directory
path (/home/jgodwin/...) is still in there, because I'm too lazy to switch it to something
else every time I commit, and I'm not savvy enough to make the script "figure out" where
everything is for you. Sorry, folks.

Summary of included files:
-ensemblemeans.py: Computes the ensemble means at each time step (6 hourly) for maximum
    temperature, minimum temperature, and accumulated precipitation. As this script runs,
    it will print out the name of the grib file it is working on, so that you can get an
    idea of its progress. This script creates two plots:
    1. ensmean_precip.png: shows the 6-hourly GEFS ensemble mean accumulated precipitation
        (liquid water, a.k.a. QPF) as bars, and the run-accumulated precipitation as a line.
        Precipitation units are in inches.
    2. ensmean_temp.png: shows the GEFS ensemble mean maximum temperature and minimum temperature
        during the preceeding 6-hour period. Temperature units are in degrees Fahrenheit.
        You will need to set your latitude and longitude manually (there are a few in there so you 
        can see what it looks like). Finally, the script creates a few CSVs that are eventually 
        read by htmlbuilder.py. These should be pretty self-explanatory. :)
-htmlbuilder.py: First off, this does not build any (meaningful) HTML yet. It's still a work in
    progress! For now, it creates some more detailed ensemble plots including plumes and box and
    whisker plots.
    1. highs.png: GEFS plume showing the daily (local time...you have to set the UTC offset
        manually!) high temperatures from each ensemble. This is done by finding the maximum
        value for each ensemble member during a 1-day period. So you'll see the daily max for
        GEP01, GEP02, etc.
    2. lows.png: same as above, but with low temperatures.
    3. precip.png: GEFS plume showing the day-over-day run-accumulated precipitation.
    4. precip_percent.png: bar chart showing the percentage of members (number of members divided
        by 20) with precipitation accumulation > 0. The numbers atop the bars are the ensemble mean
        daily precipitation amount. Why are there bars > 0%, but QPF = 0.00? This is because the
        numbers are averaged across all members, including those that have zero precip. Is this a
        "true" probability of precipitation forecast? No! Typically, the GFS Ensemble Forecast
        System is underdispersive. This means that the envelope of members tends to cluster a bit
        too much some times. If 90% of members show precipitation in 14 days, in reality, the true
        probability is probably much lower. Now if you see that 90% bar getting closer and closer,
        then it might mean something! Use this product to see things in more general terms:
        "Several members are showing some kind of QPF on Day 10" or "It looks pretty dry over the
        next couple of weeks".
    5. box_highs.png: box-and-whisker plot of daily high temperatures. The red line is the MEDIAN. 
        This is an important distiction as it is NOT THE ENSEMBLE MEAN! The boxes enclose the
        interquartile range (25th percentile to 75th percentile). In otherwords, these boxes
        enclose the half of members closest to the median. The whiskers indicate the range of the
        data (i.e. the entire guidance envelope). This is different from the default setting for
        the matplotlib box plot function.
    6. box_lows.png: same as above, but with daily lows.
    7. box_precip.png: same as above two, but with daily precipitation. This is probably the most
        useful precipitation product. The boxes give you an idea of just how many members are
        really showing appreciable precipitation. 90% of memebers might show precip, but the box
        ranges from 0.00 to 0.02...not impressive.
-get_grib.pl: Perl script courtsey of the National Centers for Environmental Prediction for
    downloading individual grib fields, instead of the entire file. This accelerates the grib
    download dramatically, and makes the scripts much faster since the grib files being passed
    through are much smaller.
    More info: http://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html.
-get_inv.pl: Also provided by NCEP, gets the grib file inventories.
-get_grib.sh: Shell script that determines which files need to be downloaded based on current time.
    This script calls EVERYTHING. It will call the two NCEP Perl scripts for downloading the data,
    then it runs the python scripts. So run this script, grab a cup of Joe, and sit back and relax.
-todolist.txt: List of tasks I hope to get to eventually. Let me know if you want any more features!
