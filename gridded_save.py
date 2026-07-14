## Get ChicagoLand counties shapefile (lake excluded)
##
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


## Emissions imports
counties = gpd.read_file('shapefiles/counties/tl_2024_us_county.shp')

def prep_chicago_gdf(inmap_gdf, chicago_counties_gdf):
	chicago_counties_gdf.to_crs(inmap_gdf.crs)

	# union into one boundary
	chicago_boundary = chicago_counties_gdf.geometry.unary_union

	# clip gdf to boundary (cuts edges)
	inmap_gdf_chicago = gpd.clip(inmap_gdf, chicago_boundary)

	return inmap_gdf_chicago

emissions_dir = '/projects/b1045/vlang/2025_ESandT_EmissionIntercomparisonPaper'

resolutions = ['1', '1_3', '4']
resolution_suffixes = {'1':'1km_cons_annual', 
					   '1_3':'1_33km_cons_annual_peryear',
					   '4':'4km_cons'}
emissions_inventories = ['ladco', 'five', 'nemo', 'uvm']

# nested dict: gdfs[res][emis_inv] = GeoDataFrame
emissions_gdfs_dict = {}

for res in resolutions:
    emissions_gdfs_dict[res] = {}

    for emis_inv in emissions_inventories:
        path = f'{emissions_dir}/{emis_inv}_{resolution_suffixes[res]}.shp'

        print(path)
        gdf = gpd.read_file(path)
        gdf_chicago = prep_chicago_gdf(gdf, chicago_counties_land)

        emissions_gdfs_dict[res][emis_inv] = gdf_chicago
        
resolutions = ['1', '1_3', '4']
emissions_inventories = ['ladco', 'five', 'nemo', 'uvm']

# nested dict: gdfs[res][emis_inv] = GeoDataFrame
gdfs_dict = {}

in_map_dir = '/projects/b1045/inmap/inmap_runs_final'

for res in resolutions:
    gdfs_dict[res] = {}

    for emis_inv in emissions_inventories:
        if emis_inv == "five" and res == "1_3":
            path = f'{in_map_dir}/{emis_inv}_{res}_km_final.shp'
        else:
            path = f'{in_map_dir}/{emis_inv}_{res}km_final.shp'

        print(path)
        gdf = gpd.read_file(path)
        gdf_chicago = prep_chicago_gdf(gdf, chicago_counties_land)

        gdfs_dict[res][emis_inv] = gdf_chicago

import pickle
import os

output_dir = "shapefiles/chicago_land_gridded/emissions"

#Save inmap grids
with open(f"{output_dir}/inmap_gdfs_dict.pkl", "wb") as f:
    pickle.dump(gdfs_dict, f)

# Save emissions grids
with open(f"{output_dir}/emissions_gdfs_dict.pkl", "wb") as f:
    pickle.dump(emissions_gdfs_dict, f)

# for res in emissions_gdfs_dict:
#     for emis in emissions_gdfs_dict[res]:
#         emissions_gdfs_dict[res][emis].to_parquet(
#             f"{output_dir}/emissions_{res}_{emis}.parquet"
#         )
        
# output_dir = "shapefiles/chicago_land_gridded/concentrations"

# for res in gdfs_dict:
#     for emis in gdfs_dict[res]:
#         gdfs_dict[res][emis].to_parquet(
#             f"{output_dir}/inmap_{res}_{emis}.parquet"
#         )
        
print("Emis Dictionaries saved.")