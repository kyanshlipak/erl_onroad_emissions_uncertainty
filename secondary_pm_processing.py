"""
putting the gridded files to chicago region
"""

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

emissions_inventories = ['five','ladco', 'nemo']
gdfs_dict = {}


in_map_dir = '/projects/b1045/inmap/shlipak_runs/output_shapefiles'


for emis_inv in emissions_inventories:
    if emis_inv == 'five':
        path = f'{in_map_dir}/{emis_inv}_1km_test.shp'
    else:
        path = f'{in_map_dir}/{emis_inv}_1km_secondary.shp'
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(chicago_counties_land.crs)
    gdf_chicago = prep_chicago_gdf(gdf, chicago_counties_land)
    gdfs_dict[emis_inv] = gdf_chicago


import pickle
output_dir = "shapefiles/secondary_pm"

#Save inmap grids
with open(f"{output_dir}/secondary_pm_concentrations_wfive.pkl", "wb") as f:
    pickle.dump(gdfs_dict, f)


"""
putting the gridded files to chicago region
"""

# ------------------------------------------------------------------------------
# Census Tract Shapefile Importing
# ------------------------------------------------------------------------------
census_tracts = gpd.read_file('shapefiles/census_tract/shapefiles/cb_2019_us_tract_500k.shp')
census_tracts_chicago_land = census_tracts.merge(
    chicago_counties_land[['STATEFP', 'COUNTYFP']].drop_duplicates(),
    on=['STATEFP', 'COUNTYFP'],
    how='inner'
)

# ------------------------------------------------------------------------------
# Census Tract Shapefile Merge with Race Data
# ------------------------------------------------------------------------------
census_tracts_chicago_race = pd.read_pickle('shapefiles/census_tract/census_tracts_chicago_race.pkl')


# ------------------------------------------------------------------------------
# Convert InMAP gridded results to census tracts
# Also read emissions census tracts and merge
# ------------------------------------------------------------------------------
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
emissions_inventories = ['ladco', 'five', 'nemo']


for inv in emissions_inventories:

	print(f"Processing INMAP: {inv}")

	grid_gdf = gdfs_dict[inv]
		
	tracts_out = aggregate_concentration_to_tracts(
		grid_gdf=grid_gdf,
		tracts_gdf=census_tracts_chicago_land,
		conc_cols=['PrimPM25', 'TotalPM25']
	)

	inmap_tract_dict[inv] = tracts_out


import pickle
output_dir = "shapefiles/secondary_pm"

# Save emissions grids
with open(f"{output_dir}/tract_concentrations_w_five.pkl", "wb") as f:
    pickle.dump(inmap_tract_dict, f)

print("Dictionaries saved.")
