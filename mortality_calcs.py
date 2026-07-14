# ------------------------------------------------------------------------------
# County Importing
# ------------------------------------------------------------------------------

import geopandas as gpd
import pandas as pd

#in_map_dir = '/projects/b1045/inmap/inmap_runs_final'
#gdf = gpd.read_file(f'{in_map_dir}/ladco_1km_final.shp')
counties = gpd.read_file('shapefiles/counties/tl_2024_us_county.shp')

##
## Get ChicagoLand counties shapefile (lake excluded)
##


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
# Grid and Census Tract Importing
# ------------------------------------------------------------------------------

import pickle

# with open("shapefiles/chicago_land_gridded/emissions_gdfs_dict.pkl", "rb") as f:
#     emissions_gdfs_dict = pickle.load(f)

# with open("shapefiles/chicago_land_gridded/inmap_gdfs_dict.pkl", "rb") as f:
#      gdfs_dict = pickle.load(f)
     
with open(f"shapefiles/rerun/conc_gdfs_dict.pkl", "rb") as f:
    conc_census_gdfs_dict = pickle.load(f)

print("Dictionaries loaded.")

# ------------------------------------------------------------------------------
# Age, Race, and BMR Data Importing
# ------------------------------------------------------------------------------
import pandas as pd
BMRs = pd.read_csv('shapefiles/census_tract/BMRs/BenMAP_mortality.csv')

BMRs['Row'] = BMRs['Row'].astype(str)
BMRs['Column'] = BMRs['Column'].astype(str)

# Format 'Row' to be a 5-digit County FIPS code
BMRs['County_FIPS'] = BMRs['Row'].str.zfill(5)

# Format 'Column' to be a 6-digit Tract FIPS code
BMRs['Tract_FIPS'] = BMRs['Column'].str.zfill(6)

# Derive State FIPS Code (first 2 digits of County FIPS)
BMRs['State_FIPS'] = BMRs['County_FIPS'].str[:2]

# Keep only county portion (last 3 digits)
BMRs['County_FIPS'] = BMRs['County_FIPS'].str[2:]

# Create GISJOIN
BMRs['GISJOIN'] = (
    'G'
    + BMRs['State_FIPS']
    + '0'
    + BMRs['County_FIPS']
    + '0'
    + BMRs['Tract_FIPS']
)

# Age range column
BMRs["Age Range"] = (
    BMRs["Start Age"].astype(str)
    + "-"
    + BMRs["End Age"].astype(str)
)

age_data  = pd.read_csv('shapefiles/census_tract/acs_age/nhgis0006_ds244_20195_tract.csv')
age_data = age_data.rename(columns={'ALT0E001': 'Total'})
# Define age range groups for summing, with column ranges for males and females
age_ranges = {
    '0-5': ['ALT0E003', 'ALT0E027'],
    '5-9': ['ALT0E004', 'ALT0E028'],
    '10-14': ['ALT0E005', 'ALT0E029'],
    '15-17': ['ALT0E006', 'ALT0E030'],
    '18-19': ['ALT0E007', 'ALT0E031'],
    '20-21': ['ALT0E008', 'ALT0E009', 'ALT0E032', 'ALT0E033'],
    '22-24': ['ALT0E010', 'ALT0E034'],
    '25-29': ['ALT0E011', 'ALT0E035'],
    '30-34': ['ALT0E012', 'ALT0E036'],
    '35-39': ['ALT0E013', 'ALT0E037'],
    '40-44': ['ALT0E014', 'ALT0E038'],
    '45-49': ['ALT0E015', 'ALT0E039'],
    '50-54': ['ALT0E016', 'ALT0E040'],
    '55-59': ['ALT0E017', 'ALT0E041'],
    '60-64': ['ALT0E018', 'ALT0E019', 'ALT0E042', 'ALT0E043'],
    '65-69': ['ALT0E020', 'ALT0E021', 'ALT0E044', 'ALT0E045'],
    '70-74': ['ALT0E022', 'ALT0E046'],
    '75-79': ['ALT0E023', 'ALT0E047'],
    '80-84': ['ALT0E024', 'ALT0E048'],
    '85+': ['ALT0E025', 'ALT0E049']
}

# Calculate total population for each age range
for age_range, columns in age_ranges.items():
    age_data[age_range] = age_data[columns].sum(axis=1)

# Drop the original columns (the ones that go ALTOM0...)
age_data = age_data.drop(columns=[col for cols in age_ranges.values() for col in cols])

# Get rid of other columns we don't need (sorry there might be a better way to do this)
for col in [
    "YEAR", "STUSAB", "REGIONA", "DIVISIONA", "STATE", "STATEA", "COUNTY", 
    "COUNTYA", "COUSUBA", "PLACEA", "TRACTA", "BLKGRPA", "CONCITA", "AIANHHA", 
    "RES_ONLYA", "TRUSTA", "AIHHTLI", "AITSCEA", "ANRCA", "CBSAA", "CSAA", 
    "METDIVA", "NECTAA", "CNECTAA", "NECTADIVA", "UAA", "CDCURRA", "SLDUA", 
    "SLDLA", "ZCTA5A", "SUBMCDA", "SDELMA", "SDSECA", "SDUNIA", "PCI", 
    "PUMAA", "GEOID", "BTTRA", "BTBGA", "NAME_E","ALT0M001", "ALT0M002", 
    "ALT0M003", "ALT0M004", "ALT0M005", "ALT0M006", "ALT0M007", "ALT0M008", 
    "ALT0M009", "ALT0M010", "ALT0M011", "ALT0M012", "ALT0M013", "ALT0M014", 
    "ALT0M015", "ALT0M016", "ALT0M017", "ALT0M018", "ALT0M019", "ALT0M020", 
    "ALT0M021", "ALT0M022", "ALT0M023", "ALT0M024", "ALT0M025", "ALT0M026", 
    "ALT0M027", "ALT0M028", "ALT0M029", "ALT0M030", "ALT0M031", "ALT0M032", 
    "ALT0M033", "ALT0M034", "ALT0M035", "ALT0M036", "ALT0M037", "ALT0M038", 
    "ALT0M039", "ALT0M040", "ALT0M041", "ALT0M042", "ALT0M043", "ALT0M044", 
    "ALT0M045", "ALT0M046", "ALT0M047", "ALT0M048", "ALT0M049", 'ALT0E002', 'ALT0E026',
    "NAME_M"]:

    del age_data[col]


def make_gisjoin_from_fips(df):
    df["STATEFP"] = df["STATEFP"].astype(str).str.zfill(2)
    df["COUNTYFP"] = df["COUNTYFP"].astype(str).str.zfill(3)
    df["TRACTCE"] = df["TRACTCE"].astype(str).str.zfill(6)

    df["GISJOIN"] = (
        "G"
        + df["STATEFP"]
        + "0"
        + df["COUNTYFP"]
        + "0"
        + df["TRACTCE"]
    )
    
    return df

census_tracts_chicago_race = pd.read_pickle('shapefiles/census_tract/census_tracts_chicago_race.pkl')
census_tracts_chicago_race = make_gisjoin_from_fips(census_tracts_chicago_race)


# first double check that age totals match race population totals
merged_check = pd.merge(census_tracts_chicago_race,
                        age_data,
                        on="GISJOIN",
                        how="inner",
                        suffixes=('_race', '_age')
                        )

print("Totals align:", (merged_check['Total_age'] -merged_check['Total_race']).value_counts())



# ------------------------------------------------------------------------------
# align population and BMR data
# ------------------------------------------------------------------------------


pivoted_df = BMRs.pivot_table(index=["GISJOIN", "Endpoint"],
                            columns="Age Range", values="Value").reset_index()

# Make df with the BMR data at the more stratified, acs age categories
age_mapping = {
    "0-0": ["0-5"],
    "1-4": ["0-5"],
    "5-14": ["5-9", "10-14"],
    "15-24": ["15-17", "18-19", "20-21", "22-24"],
    "25-34": ["25-29", "30-34"],
    "35-44": ["35-39", "40-44"],
    "45-54": ["45-49", "50-54"],
    "55-64": ["55-59", "60-64"],
    "65-74": ["65-69", "70-74"],
    "75-84": ["75-79", "80-84"],
    "85-99": ["85+"]
}

mapped_df = pd.DataFrame()
mapped_df['GISJOIN'] = pivoted_df['GISJOIN']

for mapped_range, age_ranges in age_mapping.items():
    for col in age_ranges:
        mapped_df[col] = pivoted_df[mapped_range]


"""
Merge age and mortality data to calculate baseline all-cause mortality by census tract
"""
age_with_mortality_data = pd.merge(age_data, mapped_df, on='GISJOIN', suffixes=('_population', '_mortality'))
age_with_mortality_data_chicago = age_with_mortality_data.loc[age_with_mortality_data['GISJOIN'].isin(census_tracts_chicago_race['GISJOIN'])]



# ------------------------------------------------------------------------------
# get census tract BMR (combined over age)
# ------------------------------------------------------------------------------

###
###  Compute mortality * population for each age bin over 30
###
age_bins = ['30-34', '35-39', '40-44', '45-49', '50-54', '55-59',
            '60-64', '65-69', '70-74', '75-79', '80-84']#, '85+']

# Initialize a list to store the results
baseline_mortality_rates = []

# Iterate over each GISJOIN census tract
for _, row in age_with_mortality_data_chicago.iterrows():
    total_population = row[[col + '_population' for col in age_bins]].sum()  # Sum of population for all age bins. ig this is ineffiicent but im not changing it now :(
    total_mortality = sum(row[age_bin + '_mortality'] * row[age_bin + '_population'] for age_bin in age_bins)  # Sum of mortality rate * population for each tract
    overall_mortality_rate = total_mortality / total_population if total_population != 0 else 0  # Avoid division by zero (not sure if there are any zero pop, but leavin it)
    baseline_mortality_rates.append({
        "GISJOIN": row["GISJOIN"],
       # 'GEOID': row["GEOID"],
       # 'geometry': row['geometry'],
        "total_population": total_population,
        "total_mortality": total_mortality,
        "overall_mortality_rate": overall_mortality_rate
    })

baseline_mortality_rates = pd.DataFrame(baseline_mortality_rates)

# Merge the baseline mortality rates with the original census tract GeoDataFrame to get geometry and GEOID
baseline_mortality_gdf = pd.merge(
    baseline_mortality_rates,
    census_tracts_chicago_race[['GISJOIN', 'geometry', 'GEOID']],
    on='GISJOIN',
    how='left'
)

#baseline_mortality_rates.to_csv("shapefiles/census_tract/BMRs/merged_baseline_mortality_rate.csv")

"""
I need to get census tract age data interpolated to the BMR data categories.
Except BMR data needs to be split between 30 and up and not 30 and up
I then need to merge census tract age data with BMR data
"""

# ------------------------------------------------------------------------------
# Calculations
# ------------------------------------------------------------------------------

def mortality_function(pm_mortality_data_df, pollution_col = "TotalPM25_tract", hazard_ratio = 1.08, unit = 10):
	pm_mortality_data_df = pm_mortality_data_df.copy(deep = True) # full copy so changes don't happen to the inputted df

	# divide by four because only three months of the year
	# 1.08 is per 10µg/m^3 so we divide by 10
	# real realtive risk as opposed to the relative risk function(concentration)
	pm_mortality_data_df['real_relative_risk'] = hazard_ratio ** (pm_mortality_data_df[pollution_col] / unit) 

	# attributable fraction from relative risk
	pm_mortality_data_df['AF'] = (pm_mortality_data_df['real_relative_risk'] - 1) / pm_mortality_data_df['real_relative_risk']

	# attributable mortality using (tract population) * (tract all cause mortality rate over 30) * (RWC PM attributable fraction)
	pm_mortality_data_df['Attributable_Mortality'] = pm_mortality_data_df['total_population'] * pm_mortality_data_df['overall_mortality_rate'] * pm_mortality_data_df['AF']

	# rate (population not included)
	pm_mortality_data_df['Attributable_Mortality_Rate'] = pm_mortality_data_df['overall_mortality_rate'] * pm_mortality_data_df['AF']

	# printing total estimated attributable mortalities for domain (CONUS) for the given RR
	print("RR:", hazard_ratio, " - ", round(pm_mortality_data_df['Attributable_Mortality'].sum()))
	return pm_mortality_data_df, pm_mortality_data_df[['Attributable_Mortality', 'Attributable_Mortality_Rate']]



# Dictionary to store tract-level outputs
attributable_mortality_dict = {}

summary_results = []

for res in conc_census_gdfs_dict.keys():
    attributable_mortality_dict[res] = {}
    for inv in conc_census_gdfs_dict[res].keys():

        # --- Pollution ---
        pollution_df = conc_census_gdfs_dict[res][inv]
        pollution_df = make_gisjoin_from_fips(pollution_df)

        pollution_with_bmrs = pd.merge(
            pollution_df,
            baseline_mortality_rates,
            on="GISJOIN",
            how="inner"
        )

        mortality, _ = mortality_function(pollution_with_bmrs, pollution_col = "TotalPM25_tract", hazard_ratio = 1.03, unit = 5)
        mortality.rename(columns={'Attributable_Mortality': 'PM_Attributable_Mortality', 'Attributable_Mortality_Rate': 'PM_Attributable_Mortality_Rate'}, inplace=True)

        _, mortality[['PM_Attributable_Mortality_lower', 'PM_Attributable_Mortality_Rate_lower']] = mortality_function(pollution_with_bmrs, pollution_col = "TotalPM25_tract", hazard_ratio = 1.01, unit = 5)
        _, mortality[['PM_Attributable_Mortality_upper', 'PM_Attributable_Mortality_Rate_upper']] = mortality_function(pollution_with_bmrs, pollution_col = "TotalPM25_tract", hazard_ratio = 1.04, unit = 5)

        _, mortality[['NOx_Attributable_Mortality', 'NOx_Attributable_Mortality_Rate']] = mortality_function(pollution_with_bmrs, pollution_col = "NOx_tract", hazard_ratio = 1.02, unit = 10)
        _, mortality[['NOx_Attributable_Mortality_lower', 'NOx_Attributable_Mortality_Rate_lower']] = mortality_function(pollution_with_bmrs, pollution_col = "NOx_tract", hazard_ratio = 1.01, unit = 10)
        _, mortality[['NOx_Attributable_Mortality_upper', 'NOx_Attributable_Mortality_Rate_upper']] = mortality_function(pollution_with_bmrs, pollution_col = "NOx_tract", hazard_ratio = 1.04, unit = 10)


        # -------------------------------------------------
        # Store tract-level outputs in dictionary
        # -------------------------------------------------
        attributable_mortality_dict[res][inv] = mortality

        # -------------------------------------------------
        # Summed totals for table
        # -------------------------------------------------
        pm_mid_total = round(mortality["PM_Attributable_Mortality"].sum())
        pm_low_total = round(mortality["PM_Attributable_Mortality_lower"].sum())
        pm_high_total = round(mortality["PM_Attributable_Mortality_upper"].sum())

        nox_mid_total = round(mortality["NOx_Attributable_Mortality"].sum())
        nox_low_total = round(mortality["NOx_Attributable_Mortality_lower"].sum())
        nox_high_total = round(mortality["NOx_Attributable_Mortality_upper"].sum())

        summary_results.append({
            "Res": res,
            "Emis_Inv": inv,
            "PM_Mortality": f"{pm_mid_total} ({pm_low_total}–{pm_high_total})",
            "NOx_Mortality": f"{nox_mid_total} ({nox_low_total}–{nox_high_total})"
        })

# Final table
final_table = pd.DataFrame(summary_results)[
    ["Res", "Emis_Inv", "PM_Mortality", "NOx_Mortality"]
]

final_table

import pickle
output_dir = "shapefiles/rerun"

#Save inmap grids
with open(f"{output_dir}/mortalities_dfs.pkl", "wb") as f:
    pickle.dump(attributable_mortality_dict, f)




