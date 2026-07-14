# ------------------------------------------------------------------------------
# County Importing
# ------------------------------------------------------------------------------

import geopandas as gpd

#in_map_dir = '/projects/b1045/inmap/inmap_runs_final'
#gdf = gpd.read_file(f'{in_map_dir}/ladco_1km_final.shp')
counties = gpd.read_file('shapefiles/counties/tl_2024_us_county.shp')

##
## Get ChicagoLand counties shapefile (lake excluded)
##

import pandas as pd
import geopandas as gpd

chicago_counties = ['Lake', 'McHenry', 'Cook', 'Kane', 'DuPage', 'Will', 'Kendall']

il_counties = counties.loc[(counties['STATEFP'] == '17') &
			 (counties['NAME'].isin(chicago_counties))]

# # Lake County, Indiana
# lake_in = counties.loc[
#     (counties['STATEFP'] == '18') &
#     (counties['NAME'] == 'Lake')
# ]

# combine
chicago_counties_gdf = gpd.GeoDataFrame(
    pd.concat([il_counties], ignore_index=True),
    crs=counties.crs
)
import cartopy.feature as cfeature
import shapely.geometry as sg

# --- 1️⃣ Natural Earth lakes feature ---
resol = '10m'  # can also be '50m' or '110m'
lakes_feat = cfeature.NaturalEarthFeature(
    'physical', 'lakes', scale=resol,
    edgecolor='black', facecolor=cfeature.COLORS['water']
)

# --- 2️⃣ Convert lakes to GeoDataFrame ---
lakes_gdf = gpd.GeoDataFrame(
    geometry=[geom for geom in lakes_feat.geometries()],
    crs=chicago_counties_gdf.crs
)

# --- 3️⃣ Clip the counties to remove the lake ---
chicago_counties_land = gpd.overlay(
    chicago_counties_gdf,
    lakes_gdf,
    how='difference'
)



# ------------------------------------------------------------------------------
# Census Tract Shapefile Importing
# ------------------------------------------------------------------------------
census_tracts = gpd.read_file('shapefiles/census_tract/shapefiles/cb_2019_us_tract_500k.shp')
census_tracts_chicago_land = census_tracts.merge(
    chicago_counties_land[['STATEFP', 'COUNTYFP']].drop_duplicates(),
    on=['STATEFP', 'COUNTYFP'],
    how='inner'
)


import matplotlib.pyplot as plt
import cartopy.crs as ccrs

def plot_census_tract_outlines():

	# Lambert Conformal projection (map projection)
	target_proj = ccrs.LambertConformal(
		central_longitude=-97,
		central_latitude=40,
		standard_parallels=(33, 45)
	)

	# Source CRS of the shapefile (lon/lat)
	data_crs = ccrs.PlateCarree()

	fig, ax = plt.subplots(
		figsize=(8, 8),
		subplot_kw={"projection": target_proj},
		constrained_layout=True,
		dpi=300
	)

	# Census tract boundaries
	census_tracts_chicago_land.boundary.plot(
		ax=ax,
		transform=data_crs,
		color="black",
		linewidth=0.3
	)

	# County boundaries for context
	chicago_counties_land.boundary.plot(
		ax=ax,
		transform=data_crs,
		color="red",
		linewidth=0.8
	)

	ax.set_title("Census Tracts in Chicago Counties", fontsize=16)
	ax.set_axis_off()

	plt.show()

#plot_census_tract_outlines()


# ------------------------------------------------------------------------------
# Census Tract Shapefile Merge with Race Data
# ------------------------------------------------------------------------------
# race_data = pd.read_csv('shapefiles/census_tract/acs_race/nhgis0007_race_data.csv')

# race_rename ={
#            "ALUKE001":    "Total",
#            "ALUKE003":    "White",
#            "ALUKE004":    "Black",
#            "ALUKE005":    "American Indian",
#            "ALUKE006":    "Asian",
#            "ALUKE007":    "Native Hawaiian and Other Pacific Islander",
#            "ALUKE008":    "Some Other Race",
#            "ALUKE009":    "Two or More Races",
#            'ALUKE012': 'Hispanic or Latino',
# }

# race_data = race_data.rename(columns=race_rename)
# race_data['STATEFP'] = race_data['STATEA'].astype(str).str.zfill(2)
# race_data['COUNTYFP'] = race_data['COUNTYA'].astype(str).str.zfill(3)
# race_data['TRACTCE'] = race_data['TRACTA'].astype(str).str.zfill(6)

# # Concatenate to get standard Census GEOID
# race_data['GEOID'] = race_data['STATEFP'] + race_data['COUNTYFP'] + race_data['TRACTCE']

# race_data = race_data[list(race_rename.values()) +  ['GEOID']]

# census_tracts_chicago_race = census_tracts_chicago_land.merge(
#     race_data,
#     left_on='GEOID',
#     right_on='GEOID',
#     how='left'
# )

# orig_crs = census_tracts_chicago_race.crs
# census_tracts_chicago_race = census_tracts_chicago_race.to_crs(epsg=3395)
# # Compute area in km² and population density
# census_tracts_chicago_race['area_km2'] = census_tracts_chicago_race.geometry.area / 1e6
# census_tracts_chicago_race['pop_density'] = (
# 	census_tracts_chicago_race['Total'] / census_tracts_chicago_race['area_km2']
# )
# census_tracts_chicago_race = census_tracts_chicago_race.to_crs(orig_crs)

# census_tracts_chicago_race['Hispanic'] = census_tracts_chicago_race['Hispanic or Latino']
# census_tracts_chicago_race.to_pickle("shapefiles/census_tract/census_tracts_chicago_race.pkl")

census_tracts_chicago_race = pd.read_pickle("shapefiles/census_tract/census_tracts_chicago_race.pkl")

# Project to a metric CRS to compute area in m²
def population_plot(census_tracts_chicago_race, col, vmin, vmax):
	# sanity check

	target_proj = ccrs.LambertConformal(
		central_longitude=-97,
		central_latitude=40,
		standard_parallels=(33, 45)
	)

	data_crs = ccrs.PlateCarree()

	fig, ax = plt.subplots(
		figsize=(10, 10),
		subplot_kw={"projection": target_proj},
		constrained_layout=True,
		dpi=300
	)

	# Plot population density choropleth
	census_tracts_chicago_race.plot(
		column=col,
		ax=ax,
		transform=data_crs,
		cmap='viridis',
		linewidth=0.2,
		edgecolor='gray',
		legend=True, 
		vmin = vmin,
		vmax = vmax
	)

	# County boundaries for context
	chicago_counties_land.boundary.plot(
		ax=ax,
		transform=data_crs,
		color='black',
		linewidth=0.8
	)

	ax.set_title(f"{col} – Chicago Census Tracts", fontsize=16)
	ax.set_axis_off()

	plt.show()

# population_plot(census_tracts_chicago_race, 'pop_density', 0, 6000)

# census_tracts_chicago_race['black_pct'] = 100* census_tracts_chicago_race['Black']/census_tracts_chicago_race['Total']
# population_plot(census_tracts_chicago_race, 'black_pct', 0, 100)

# census_tracts_chicago_race['asian_pct'] = 100* census_tracts_chicago_race['Asian']/census_tracts_chicago_race['Total']
# population_plot(census_tracts_chicago_race, 'asian_pct', 0, 50)




# ------------------------------------------------------------------------------
# Convert InMAP gridded results to census tracts
# Also read emissions census tracts and merge
# ------------------------------------------------------------------------------


import pickle

#with open("shapefiles/chicago_land_gridded/inmap_gdfs_dict.pkl", "rb") as f:
with open("shapefiles/rerun/inmap_gdfs_dict.pkl", "rb") as f:
    gdfs_dict = pickle.load(f)

print("Dictionaries loaded.")

def aggregate_concentration_to_tracts(
    grid_gdf,
    tracts_gdf,
    conc_cols,
    target_crs="EPSG:3395"
):
    """
    Area-weight concentration from grid polygons to census tracts.
    """

    # Copy
    grid = grid_gdf.copy()
    tracts = tracts_gdf.copy()
    orig_crs = tracts.crs

    # Project to metric CRS
    grid = grid.to_crs(target_crs)
    tracts = tracts.to_crs(target_crs)

    # Spatial intersection
    intersect = gpd.overlay(
        grid,
        tracts[['GEOID', 'geometry']],
        how='intersection'
    )

    # Area in m²
    intersect['area_m2'] = intersect.geometry.area

    tract_results = []

    for col in conc_cols:

        temp = (
            intersect
            .assign(weighted=lambda x: x[col] * x['area_m2'])
            .groupby('GEOID')[['weighted', 'area_m2']]
            .sum()
        )

        temp[f"{col}_tract"] = temp['weighted'] / temp['area_m2']
        tract_results.append(temp[f"{col}_tract"])

    tract_conc_df = pd.concat(tract_results, axis=1)

    tracts_out = tracts.join(tract_conc_df, on='GEOID')
    tracts_out = tracts_out.to_crs(orig_crs)

    return tracts_out


inmap_tract_dict = {}

resolutions = ['1', '1_3', '4']
emissions_inventories = ['ladco', 'five', 'nemo', 'uvm']

for res in resolutions:
	inmap_tract_dict[res] = {}

	for inv in emissions_inventories:

		print(f"Processing INMAP: {inv}, resolution {res}")

		grid_gdf = gdfs_dict[res][inv]
            
		tracts_out = aggregate_concentration_to_tracts(
			grid_gdf=grid_gdf,
			tracts_gdf=census_tracts_chicago_land,
			conc_cols=['NOx', 'TotalPM25']
		)

		inmap_tract_dict[res][inv] = tracts_out

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

def plot_tract_flux(gdf, column, title):

    # Lambert Conformal projection
    target_proj = ccrs.LambertConformal(
        central_longitude=-97,
        central_latitude=40,
        standard_parallels=(33, 45)
    )

    # Source CRS (assuming your GeoDataFrame is lon/lat)
    data_crs = ccrs.PlateCarree()

    fig, ax = plt.subplots(
        figsize=(8, 8),
        subplot_kw={"projection": target_proj},
        constrained_layout=True,
        dpi=300
    )

    # Optional: clip extreme values for visualization sanity
    vmin = gdf[column].quantile(0.02)
    vmax = gdf[column].quantile(0.98)

    # Filled census tracts
    gdf.plot(
        column=column,
        ax=ax,
        transform=target_proj,
        cmap="viridis",
        linewidth=0,
        vmin=vmin,
        vmax=vmax,
        legend=True
    )

    # County boundaries for context
    chicago_counties_land.boundary.plot(
        ax=ax,
        transform=target_proj,
        color="red",
        linewidth=0.8
    )

    ax.set_title(title, fontsize=16)
    ax.set_axis_off()

    plt.show()


# plot_tract_flux(
#     inmap_tract_dict['1']['nemo'],
#     column="TotalPM25_tract",
#     title="PM2.5 Conc. by Census Tract (1km NEMO)"
# )

###
### pickle the census tract emissions flux dictionary 
###

import pickle
output_dir = "shapefiles/rerun"

# Save emissions grids
with open(f"{output_dir}/conc_gdfs_dict.pkl", "wb") as f:
    pickle.dump(inmap_tract_dict, f)

print("Dictionaries saved.")



# ------------------------------------------------------------------------------
# read gridded emissions to census tract
# ------------------------------------------------------------------------------

###
### read emissions gridded dict
###

with open("shapefiles/chicago_land_gridded/emissions_gdfs_dict.pkl", "rb") as f:
    emissions_gdfs_dict = pickle.load(f)
print("Dictionaries loaded.")

def aggregate_flux_to_tracts(
    grid_gdf,
    tracts_gdf,
    pollutant_cols,
    flux_scale_factor=24*365,
    target_crs="EPSG:3395"
):
    """
    Area-weight emission flux from grid polygons to census tracts.

    Parameters
    ----------
    grid_gdf : GeoDataFrame
        Emissions grid (must contain pollutant columns).
    tracts_gdf : GeoDataFrame
        Census tract polygons with GEOID column.
    pollutant_cols : list
        List of pollutant column names in grid_gdf (e.g., ['PM25','NOX']).
    flux_scale_factor : float
        Factor to scale raw emissions (default converts g/s → tons/year/km² if already per km²).
    target_crs : str
        Projected CRS for area calculations.

    Returns
    -------
    tracts_out : GeoDataFrame
        Census tracts with aggregated pollutant flux columns added.
    """

    # Copy to avoid modifying originals
    grid = grid_gdf.copy()
    tracts = tracts_gdf.copy()

    # Scale pollutants to flux units
    for pol in pollutant_cols:
        grid[f"{pol}_flux"] = grid[pol] * flux_scale_factor

    # Project to metric CRS
    grid = grid.to_crs(target_crs)
    tracts = tracts.to_crs(target_crs)

    # Spatial intersection
    intersect = gpd.overlay(
        grid,
        tracts[['GEOID', 'geometry']],
        how='intersection'
    )

    # Area of each intersection in km²
    intersect['area_km2'] = intersect.geometry.area / 1e6

    # Aggregate each pollutant
    tract_results = []

    for pol in pollutant_cols:
        flux_col = f"{pol}_flux"

        temp = (
            intersect
            .assign(weighted=lambda x: x[flux_col] * x['area_km2'])
            .groupby('GEOID')[['weighted', 'area_km2']]
            .sum()
        )

        temp[f"{pol}_flux_tract"] = temp['weighted'] / temp['area_km2']
        tract_results.append(temp[f"{pol}_flux_tract"])

    # Combine all pollutants into one dataframe
    tract_flux_df = gpd.GeoDataFrame(pd.concat(tract_results, axis=1))

    # Join back to tracts
    tracts_out = tracts.join(tract_flux_df, on='GEOID')

    # Return to original CRS
    tracts_out = tracts_out.to_crs(tracts_gdf.crs)

    return tracts_out

###
### Double checking it all works okay by plotting PM2.5 flux by tract
###

# gdf = emissions_gdfs_dict['1']['ladco']

# tracts_emis = aggregate_flux_to_tracts(
#     grid_gdf=gdf,
#     tracts_gdf=census_tracts_chicago_land,
#     pollutant_cols=['PM25', 'NOX'],
#     flux_scale_factor=24*365
# )

# plot_tract_flux(
#     tract_flux_dict['4']['nemo'],
#     column="PM25_flux_tract",
#     title="PM2.5 Flux by Census Tract (4km NEMO)"
# )


###
### convert sand save to dict
###

### Now loop through all inventories and resolutions, save census tract emissions to dict
tract_flux_dict = {}

resolutions = ['1', '1_3', '4']
emissions_inventories = ['ladco', 'five', 'nemo', 'uvm']

for res in resolutions:

	tract_flux_dict[res] = {}

	for inv in emissions_inventories:
		
		print(f"Aggregating resolution {res}, inventory {inv}")
		grid_gdf = emissions_gdfs_dict[res][inv]
		
		if res == '1_3': flux_scale_factor=1/(1.3**2)
		else: flux_scale_factor=24*365

		tracts_emis = aggregate_flux_to_tracts(
			grid_gdf=grid_gdf,
			tracts_gdf=census_tracts_chicago_land,
			pollutant_cols=['PM25', 'NOX'],
			flux_scale_factor=flux_scale_factor
		)
		
		tract_flux_dict[res][inv] = tracts_emis

###
### pickle the census tract emissions flux dictionary 
###

import pickle
output_dir = "shapefiles/census_tract"

# Save emissions grids
with open(f"{output_dir}/emissions_gdfs_dict.pkl", "wb") as f:
    pickle.dump(tract_flux_dict, f)

print("Dictionaries saved.")


