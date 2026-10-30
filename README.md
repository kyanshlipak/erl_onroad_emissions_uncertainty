## census_tract_merging.py
Spatial aggregation to get gridded emissions or concentrations to the census tract level. Area-weighted averaging was used.

## gridded_save.py
Clip the larger InMAP or emissions inventory domains to the Greater Chicago Region. Create a dictionary that organizes the shapefiles by resolution and inventory., Save to pickle for easy future loading and analyses.

## mort_county_calcs.py
Compute attributable mortality calculations using only county-level baseline mortality data.

## mortality_calcs.py
Compute attributable mortality calculations at the census tract level.

## prep_for_comparison.py
Prep data from Visa et al. for comparison with InMAP simulated data at 1.3 km.

## secondary_pm_processing,py
Processing outputs from simulations with additional secondary PM2.5 precursors for a sensitivity analysis. Actual comparison figures and stats are done in spatial_plots.ipynb.

## spatial_plots.ipynb
Make figures! All the tables and figures in the main text and SI came from here.

## requirements.txt
The Python libraries and versions required to run everything here.
