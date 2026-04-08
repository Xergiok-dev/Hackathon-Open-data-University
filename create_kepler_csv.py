"""
Convert dpe_enedis_joined.csv to Kepler.gl compatible format
by cleaning up column names and removing problematic values
"""

import pandas as pd
import numpy as np

# Load the joined data
df = pd.read_csv("data/dpe_enedis_joined.csv", low_memory=False)

print(f"Original data: {len(df):,} rows, {len(df.columns)} columns")

# Keep only essential columns for mapping
essential_cols = [
    'lat', 'lon', 'annee', 'classe_dpe_modale', 'adresse',
    'conso_par_logement_kwh', 'surface_med', 'nb_dpe'
]

# Select available columns
available_cols = [col for col in essential_cols if col in df.columns]
df_kepler = df[available_cols].copy()

print(f"Selected columns: {available_cols}")

# Clean data for Kepler.gl
# Remove rows with missing lat/lon (critical for mapping)
df_kepler = df_kepler.dropna(subset=['lat', 'lon'])

# Replace NaN with 0 or empty string for other columns
for col in df_kepler.columns:
    if col not in ['lat', 'lon']:
        if df_kepler[col].dtype in ['float64', 'int64']:
            df_kepler[col] = df_kepler[col].fillna(0)
        else:
            df_kepler[col] = df_kepler[col].fillna('')

# Rename columns to remove special characters
df_kepler = df_kepler.rename(columns={
    'classe_dpe_modale': 'dpe_class',
    'conso_par_logement_kwh': 'consumption_kwh',
    'surface_med': 'surface_m2',
    'nb_dpe': 'num_dpe_records',
    'annee': 'year'
})

# Ensure numeric columns are actually numeric
for col in ['lat', 'lon', 'consumption_kwh', 'surface_m2']:
    if col in df_kepler.columns:
        df_kepler[col] = pd.to_numeric(df_kepler[col], errors='coerce')

# Remove any remaining rows with NaN in critical columns
df_kepler = df_kepler.dropna(subset=['lat', 'lon'])

# Round coordinates for cleaner display
df_kepler['lat'] = df_kepler['lat'].round(6)
df_kepler['lon'] = df_kepler['lon'].round(6)

# Save new CSV
output_file = "data/kepler_data.csv"
df_kepler.to_csv(output_file, index=False)

print(f"\n✓ Kepler.gl data saved → {output_file}")
print(f"  Rows: {len(df_kepler):,}")
print(f"  Columns: {list(df_kepler.columns)}")
print(f"\nData preview:")
print(df_kepler.head(10))
