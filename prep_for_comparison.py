"""
1. subtract all_vehicles from base for each season
2. average difference across seasons
3. convert into shapefile
4. plot spatially
5. put the shp into a pkl
"""

import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import pyproj
import pickle
import matplotlib.pyplot as plt

base_dir = '/projects/b1045/wrf-cmaq/output/Chicago_LADCO/'

dirs_all_vehicles = [
    'output_Maxime_allTransport_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_Maxime_allTransport_fall_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_Maxime_allTransport_spring_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_Maxime_allTransport_wint_1.33km_sf_rrtmg_5_8_1_v3852'
]

dirs_base = [
    'output_BASE_FINAL_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_BASE_FINAL_fall_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_BASE_FINAL_spring_1.33km_sf_rrtmg_5_8_1_v3852',
    'output_BASE_FINAL_wint_1.33km_sf_rrtmg_5_8_1_v3852'
]

VAR = 'PM25_TOT'
SURFACE_LAY = 0


def load_surface(dir_list):
    """Load VAR surface layer (already time-averaged) from each seasonal dir."""
    arrs = []
    ref = None
    for d in dir_list:
        file = base_dir + d + '/postprocess/avg.nc'
        ds = xr.open_dataset(file)
        if ref is None:
            ref = ds

        da = ds[VAR]
        if 'LAY' in da.dims:
            da = da.isel(LAY=SURFACE_LAY)
        if 'TSTEP' in da.dims:
            da = da.isel(TSTEP=0)

        arrs.append(da)
        print(f'Loaded {VAR} from {file}, shape {da.shape}')
    return arrs, ref


# ---------------------------------------------------------------------------
# 1. Subtract all_vehicles from base, per season
# ---------------------------------------------------------------------------
base_arrs, ref_ds = load_surface(dirs_base)
allveh_arrs, _ = load_surface(dirs_all_vehicles)

season_diffs = []
for base_da, allveh_da in zip(base_arrs, allveh_arrs):
    diff = base_da - allveh_da
    season_diffs.append(diff)

# ---------------------------------------------------------------------------
# 2. Average the difference across seasons
# ---------------------------------------------------------------------------
stacked_diff = xr.concat(season_diffs, dim='season')
mean_diff = stacked_diff.mean(dim='season')

arr = np.asarray(mean_diff.values).squeeze()
print('Averaged difference array shape:', arr.shape)

# ---------------------------------------------------------------------------
# 3. Convert into shapefile (grid-cell polygons, EPSG:4326)
# ---------------------------------------------------------------------------
attrs = ref_ds.attrs
xorig = float(attrs['XORIG'])
yorig = float(attrs['YORIG'])
xcell = float(attrs['XCELL'])
ycell = float(attrs['YCELL'])

truelat1 = float(attrs.get('P_ALP', attrs.get('TRUELAT1')))
truelat2 = float(attrs.get('P_BET', attrs.get('TRUELAT2')))
stand_lon = float(attrs.get('P_GAM', attrs.get('STAND_LON')))
cen_lat = float(attrs.get('YCENT', attrs.get('MOAD_CEN_LAT', truelat1)))
cen_lon = stand_lon

lcc_crs = pyproj.CRS.from_proj4(
    f"+proj=lcc +lat_1={truelat1} +lat_2={truelat2} +lat_0={cen_lat} "
    f"+lon_0={cen_lon} +x_0=0 +y_0=0 +a=6370000 +b=6370000 +units=m +no_defs"
)

nrows, ncols = arr.shape

polygons = []
values = []
rows = []
cols = []

for r in range(nrows):
    y0 = yorig + r * ycell
    y1 = y0 + ycell
    for c in range(ncols):
        x0 = xorig + c * xcell
        x1 = x0 + xcell
        polygons.append(box(x0, y0, x1, y1))
        values.append(arr[r, c])
        rows.append(r)
        cols.append(c)

gdf = gpd.GeoDataFrame(
    {'ROW': rows, 'COL': cols, 'PM25_TOT_diff': values},
    geometry=polygons,
    crs=lcc_crs
)

gdf_wgs84 = gdf.to_crs(epsg=4326)

out_path = 'shapefiles/base_minus_allvehicles_annual_mean.shp'
gdf_wgs84.to_file(out_path)
print(f'Wrote shapefile to {out_path}, {len(gdf_wgs84)} grid cells')

# ---------------------------------------------------------------------------
# 4. Plot spatially
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 8))
gdf_wgs84.plot(column='PM25_TOT_diff', cmap='viridis', legend=True, ax=ax)
ax.set_title('Base - All Vehicles: Annual Mean PM25_TOT Difference')
plt.savefig('shapefiles/base_minus_allvehicles_annual_mean.png', dpi=150, bbox_inches='tight')
plt.show()


"""
Clip gridded PM25_TOT difference to Chicago-area counties (lake excluded)
"""
import geopandas as gpd
import pandas as pd
import cartopy.feature as cfeature

## Get ChicagoLand counties shapefile (lake excluded)
counties = gpd.read_file('shapefiles/counties/tl_2024_us_county.shp')

chicago_counties = ['Lake', 'McHenry', 'Cook', 'Kane', 'DuPage', 'Will', 'Kendall']

il_counties = counties.loc[(counties['STATEFP'] == '17') &
                            (counties['NAME'].isin(chicago_counties))]

chicago_counties_gdf = gpd.GeoDataFrame(
    pd.concat([il_counties], ignore_index=True),
    crs=counties.crs
)

# --- Natural Earth lakes feature ---
resol = '10m'
lakes_feat = cfeature.NaturalEarthFeature(
    'physical', 'lakes', scale=resol,
    edgecolor='black', facecolor=cfeature.COLORS['water']
)

lakes_gdf = gpd.GeoDataFrame(
    geometry=[geom for geom in lakes_feat.geometries()],
    crs=chicago_counties_gdf.crs
)

chicago_counties_land = gpd.overlay(
    chicago_counties_gdf,
    lakes_gdf,
    how='difference'
)

# --- Clip the PM25_TOT diff grid to the Chicago counties boundary ---
gdf_wgs84_to_clip = gdf_wgs84.to_crs(chicago_counties_land.crs)
chicago_boundary = chicago_counties_land.geometry.unary_union
gdf_chicago = gpd.clip(gdf_wgs84_to_clip, chicago_boundary)

# --- Plot the clipped result ---
fig, ax = plt.subplots(figsize=(10, 8))
gdf_chicago.plot(column='PM25_TOT_diff', cmap='RdBu_r', legend=True, ax=ax)
chicago_counties_land.boundary.plot(ax=ax, color='black', linewidth=0.5)
ax.set_title('Base - All Vehicles: Annual Mean PM25_TOT Difference (Chicago Counties)')
plt.show()

# --- Save clipped shapefile and pickle ---
gdf_chicago.to_file('shapefiles/base_minus_allvehicles_annual_mean_chicago.shp')

import pickle
with open('shapefiles/base_minus_allvehicles_annual_mean_chicago.pkl', 'wb') as f:
    pickle.dump(gdf_chicago, f)



