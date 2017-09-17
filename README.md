# gefs-plots
Plots GEFS Ensemble data

get_grib.pl and get_inv.pl are scripts provided courtesy of the NOAA Climate Prediction Center for downloading individual grib fields. This accelerates the grib download significantly. More information here: http://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html.

htmlbuilder.py - This program will (eventually) create a webpage containing a table displaying the individual member high/low and precipitation forecasts, with the table colorized according to 1981-2010 temperature anomalies. This script is still under construction.

temp_plotter.py - This program reads the grib files, plots the ensemble mean, and generates CSV files containing the ensemble member data.
