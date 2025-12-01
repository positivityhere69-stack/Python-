# weather_visualizer.py
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------

# -------------------------
INPUT_CSV = "wheather_data.csv.csv"  
CLEANED_CSV = "cleaned_weather.csv"
OUTPUT_DIR = "weather_outputs"
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary_report.txt")

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------
# Helper functions
# -------------------------
def safe_read_csv(path):
    """Read CSV with common encodings and return DataFrame."""
    try:
        df = pd.read_csv(path)
        return df
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='latin1')
    except Exception as e:
        print(f"Error reading {path}: {e}")
        sys.exit(1)

def detect_date_column(df):
    """Try to detect a date column name from common names."""
    candidates = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
    if candidates:
        return candidates[0]

    first = df.columns[0]
    sample = df[first].astype(str).iloc[:5].str.replace('-', '').str.replace('/', '')
    if sample.str.isnumeric().any():
        return first
    return None

def parse_dates(df, date_col):
    """Convert date column to datetime, create day/month/year columns."""
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    
    df = df.dropna(subset=[date_col]).copy()
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    df = df.set_index(date_col)
    return df

def basic_cleaning(df):
    """Lowercase column names, strip spaces, convert numeric-like cols to numeric."""
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    for c in df.columns:
        
        if df[c].dtype == object:
        
            coerced = pd.to_numeric(df[c].str.replace('[^\d\.\-]', '', regex=True), errors='coerce')
            # if lots of numeric present, replace
            if coerced.notna().sum() > len(df) * 0.1:
                df[c] = coerced
    return df

def fill_missing(df, strategy_cols=None):
    """Fill NaNs: numeric -> interpolate then fill with mean; categorical -> fill mode."""
    # interpolate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df[numeric_cols] = df[numeric_cols].interpolate(limit_direction='both')
    # fill remaining numeric NaNs with column mean
    for c in numeric_cols:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].mean())
    # categorical columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    for c in cat_cols:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].mode().iloc[0] if not df[c].mode().empty else "")
    return df

def compute_statistics(df, numeric_cols):
    stats = {}
    for c in numeric_cols:
        col = df[c].dropna()
        if col.empty:
            continue
        stats[c] = {
            'mean': float(np.mean(col)),
            'min': float(np.min(col)),
            'max': float(np.max(col)),
            'std': float(np.std(col, ddof=1))
        }
    return stats

def save_plot(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, bbox_inches='tight')
    print(f"Saved plot: {path}")

# -------------------------
# Main process
# -------------------------
def main():
    print("Starting Weather Data Visualizer...")

    if not os.path.exists(INPUT_CSV):
        print(f"Input CSV '{INPUT_CSV}' not found. Please place it in this folder or change INPUT_CSV variable.")
        sys.exit(1)

    # 1. Load
    df = safe_read_csv(INPUT_CSV)
    print("Columns found:", list(df.columns))

    # 2. Detect and parse date
    date_col = detect_date_column(df)
    if date_col is None:
        print("Could not detect a date column automatically. Ensure your CSV has a date/time column.")
        sys.exit(1)
    print(f"Using '{date_col}' as date column.")
    df = parse_dates(df, date_col)

    # 3. Clean columns
    df = basic_cleaning(df)

    # 4. Try to identify likely important columns
    cols = df.columns.tolist()
    # common names mapping
    def find_col(keywords):
        for k in keywords:
            for c in cols:
                if k in c:
                    return c
        return None

    temp_col = find_col(['temp', 'temperature', 't_avg', 't_mean', 'tmax', 'tmin'])
    rain_col = find_col(['rain', 'precip', 'ppt', 'rainfall'])
    humidity_col = find_col(['humid', 'rh', 'relative_humidity'])

    print("Detected columns -> temperature:", temp_col, "rainfall:", rain_col, "humidity:", humidity_col)

    # 5. Fill missing
    df = fill_missing(df)

    # 6. Compute stats
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    stats = compute_statistics(df, numeric_cols)

    # 7. Save cleaned CSV
    df.reset_index(inplace=True)  # make date a column again for saving
    df.to_csv(CLEANED_CSV, index=False)
    print(f"Cleaned data saved to {CLEANED_CSV}")

    # 8. Plots
    # Re-index by date if needed
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)

    # (A) Line chart: daily temperature trend (if temperature column exists)
    if temp_col and temp_col in df.columns:
        fig, ax = plt.subplots(figsize=(10,4))
        ax.plot(df.index, df[temp_col])
        ax.set_title("Daily Temperature Trend")
        ax.set_xlabel("Date")
        ax.set_ylabel(temp_col.replace('_',' ').title())
        fig.autofmt_xdate()
        save_plot(fig, "daily_temperature_trend.png")
        plt.close(fig)
    else:
        print("Temperature column not found — skipping daily temperature plot.")

    # (B) Bar chart: monthly rainfall totals (if rainfall column exists)
    if rain_col and rain_col in df.columns:
        monthly_rain = df[rain_col].resample('M').sum()
        fig, ax = plt.subplots(figsize=(10,4))
        ax.bar(monthly_rain.index.strftime("%Y-%m"), monthly_rain.values)
        ax.set_title("Monthly Rainfall Totals")
        ax.set_xlabel("Month")
        ax.set_ylabel(f"Total {rain_col}")
        plt.xticks(rotation=45)
        save_plot(fig, "monthly_rainfall_totals.png")
        plt.close(fig)
    else:
        print("Rainfall column not found — skipping monthly rainfall plot.")

    # (C) Scatter: humidity vs temperature
    if temp_col and humidity_col and temp_col in df.columns and humidity_col in df.columns:
        subset = df[[temp_col, humidity_col]].dropna()
        fig, ax = plt.subplots(figsize=(6,6))
        ax.scatter(subset[temp_col], subset[humidity_col], alpha=0.6)
        ax.set_title("Humidity vs Temperature")
        ax.set_xlabel(temp_col.replace('_',' ').title())
        ax.set_ylabel(humidity_col.replace('_',' ').title())
        save_plot(fig, "humidity_vs_temperature.png")
        plt.close(fig)
    else:
        print("Temperature or humidity column missing — skipping scatter plot.")



    combined_created = False
    try:
        monthly_mean_temp = df[temp_col].resample('M').mean() if temp_col in df.columns else None
        monthly_total_rain = df[rain_col].resample('M').sum() if rain_col in df.columns else None

        if monthly_mean_temp is not None and monthly_total_rain is not None:
            fig, axes = plt.subplots(1,2, figsize=(14,4))
            axes[0].plot(monthly_mean_temp.index, monthly_mean_temp.values)
            axes[0].set_title("Monthly Mean Temperature")
            axes[0].set_xlabel("Month")
            axes[0].set_ylabel(temp_col.replace('_',' ').title())
            axes[0].tick_params(axis='x', rotation=45)

            axes[1].bar(monthly_total_rain.index.strftime("%Y-%m"), monthly_total_rain.values)
            axes[1].set_title("Monthly Total Rainfall")
            axes[1].set_xlabel("Month")
            axes[1].set_ylabel(f"Total {rain_col}")
            axes[1].tick_params(axis='x', rotation=45)

            save_plot(fig, "combined_monthly_temp_rain.png")
            plt.close(fig)
            combined_created = True
    except Exception as e:
        print("Error creating combined plot:", e)

    if not combined_created:
        print("Combined monthly plot skipped (missing temp or rainfall).")

    
    agg_table = None
    try:
        agg_table = df.resample('M').agg({
            temp_col: ['mean','min','max'] if temp_col in df.columns else {},
            rain_col: ['sum','mean'] if rain_col in df.columns else {},
            humidity_col: ['mean'] if humidity_col in df.columns else {}
        })
        # flatten columns
        agg_table.columns = ['_'.join(filter(None, map(str, col))).strip() for col in agg_table.columns.values]
        agg_csv_path = os.path.join(OUTPUT_DIR, "monthly_aggregates.csv")
        agg_table.to_csv(agg_csv_path)
        print(f"Monthly aggregates saved to {agg_csv_path}")
    except Exception as e:
        print("Could not compute monthly aggregates:", e)

    # 10. Create summary report
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        f.write("Weather Data Visualizer - Summary Report\n")
        f.write(f"Generated on: {datetime.now().isoformat()}\n\n")
        f.write("Input file: " + INPUT_CSV + "\n")
        f.write("Cleaned file: " + CLEANED_CSV + "\n\n")

        f.write("Detected key columns:\n")
        f.write(f"  Temperature column: {temp_col}\n")
        f.write(f"  Rainfall column: {rain_col}\n")
        f.write(f"  Humidity column: {humidity_col}\n\n")

        f.write("Basic numeric statistics (sample):\n")
        for col, s in stats.items():
            f.write(f"- {col}: mean={s['mean']:.3f}, min={s['min']:.3f}, max={s['max']:.3f}, std={s['std']:.3f}\n")

        f.write("\nGenerated plots (saved in output folder):\n")
        f.write("  - daily_temperature_trend.png\n")
        f.write("  - monthly_rainfall_totals.png\n")
        f.write("  - humidity_vs_temperature.png\n")
        f.write("  - combined_monthly_temp_rain.png\n")
        f.write("\nNotes:\n")
        f.write(" - Missing numeric values were interpolated then filled with column means if necessary.\n")
        f.write(" - Date parsing used day-first convention; if your dates are in another format, adjust parse logic.\n")
        f.write("\nEnd of report.\n")

    print(f"Summary report saved to {SUMMARY_FILE}")
    print("All done. Check the outputs folder for images and the cleaned CSV.")

if __name__ == "__main__":
    main()
