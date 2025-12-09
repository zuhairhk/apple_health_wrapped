import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# --- Configuration ---
XML_FILE_PATH = 'export.xml'
TARGET_YEAR = 2025
SLEEP_TYPE = 'HKCategoryTypeIdentifierSleepAnalysis'

# --- Utility Functions ---

def time_to_adjusted_seconds(t, is_bedtime):
    """Converts time object to adjusted seconds from midnight for averaging."""
    seconds = t.hour * 3600 + t.minute * 60 + t.second
    # Shift bedtime forward 24 hours if it is before noon
    if is_bedtime and t.hour < 12:
        seconds += 86400
    return seconds

def seconds_to_time_str(seconds):
    """Converts adjusted seconds back to a HH:MM:SS time string."""
    return (datetime.min + timedelta(seconds=int(seconds) % 86400)).strftime('%H:%M:%S')

def create_adjusted_bedtime_dt(row):
    """Creates a date-aware datetime object, shifting post-midnight bedtimes."""
    dt = row['start']
    # If sleep starts after midnight (e.g., 1AM), treat it as 25:00 on the previous day's cycle
    if dt.hour < 12:
        return dt + timedelta(days=1)
    return dt

def analyze_sleep_data(file_path, year):

    print(f"Loading data from {file_path}...")

    # Load XML safely
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error loading XML: {e}")
        return

    sleep_records = []

    # Extract raw asleep segments (HKCategoryValueSleepAnalysisAsleep* values)
    for record in root.iter('Record'):
        if record.get('type') != SLEEP_TYPE:
            continue

        value = record.get("value", "")
        # Only include records that indicate the user was actually 'Asleep'
        if "Asleep" not in value:
            continue

        start = record.get("startDate")
        end = record.get("endDate")
        if not start or not end:
            continue

        try:
            end_year = datetime.strptime(end.split(" ")[0], "%Y-%m-%d").year
        except ValueError:
            continue
            
        if end_year != year:
            continue

        sleep_records.append(record.attrib)

    if not sleep_records:
        print(f"No sleep data for {year}.")
        return

    # --- Convert to DataFrame ---
    df = pd.DataFrame(sleep_records)
    date_format = "%Y-%m-%d %H:%M:%S %z"
    df["startDate"] = pd.to_datetime(df["startDate"], format=date_format)
    df["endDate"] = pd.to_datetime(df["endDate"], format=date_format)

    # --- Merge overlapping/consecutive intervals (to treat a full night as one block) ---
    df_sorted = df.sort_values("startDate").reset_index(drop=True)

    merged = []
    for i, row in df_sorted.iterrows():
        start = row["startDate"]
        end = row["endDate"]

        if not merged:
            merged.append({'start': start, 'end': end, 'Sleep_Day': end.normalize()})
        else:
            last_entry = merged[-1]
            last_start, last_end = last_entry['start'], last_entry['end']
            
            # Merge if the new segment starts before the last segment ends (plus a small buffer, e.g., 5 min)
            if start <= last_end + timedelta(minutes=5):
                last_entry['end'] = max(last_end, end)
            else:
                merged.append({'start': start, 'end': end, 'Sleep_Day': end.normalize()})

    merged_df = pd.DataFrame(merged)
    # Filter merged blocks by target year (using the wake-up date)
    merged_df = merged_df[merged_df["end"].dt.year == year].copy()

    # --- Calculate metrics for merged blocks ---
    merged_df["Hours_Slept"] = (merged_df["end"] - merged_df["start"]).dt.total_seconds() / 3600.0
    merged_df["Bed_Time"] = merged_df["start"].dt.time
    merged_df["Wake_Time"] = merged_df["end"].dt.time
    
    # Add adjusted start/end datetime objects for min/max
    merged_df["start_adj_dt"] = merged_df.apply(create_adjusted_bedtime_dt, axis=1)

    # --- Daily Sleep Aggregation (One row per unique wake-up day) ---
    daily_sleep = merged_df.groupby('Sleep_Day')['Hours_Slept'].sum().reset_index()
    daily_sleep.columns = ["Date", "Hours_Slept"]

    # FIX: Correct Total Days with Data (uses unique days from the aggregation)
    total_days = len(daily_sleep)
    total_hours = daily_sleep["Hours_Slept"].sum()
    avg_sleep = total_hours / total_days if total_days else 0

    longest = daily_sleep.loc[daily_sleep["Hours_Slept"].idxmax()]
    shortest = daily_sleep.loc[daily_sleep["Hours_Slept"].idxmin()]

    # --- Bed/Wake Time Metrics (using adjusted seconds) ---
    
    # Convert time objects to adjusted seconds for mode/std dev
    merged_df["Bed_Seconds_Adjusted"] = merged_df["Bed_Time"].apply(lambda t: time_to_adjusted_seconds(t, True))
    merged_df["Wake_Seconds"] = merged_df["Wake_Time"].apply(lambda t: time_to_adjusted_seconds(t, False))
    
    # --- MODE (Binning to nearest 15 minutes) ---
    bin_size_sec = 900 # 15 minutes
    
    # FIX: Corrected rounding logic (S / N).round() * N
    bed_binned_sec = (merged_df["Bed_Seconds_Adjusted"] / bin_size_sec).round() * bin_size_sec
    wake_binned_sec = (merged_df["Wake_Seconds"] / bin_size_sec).round() * bin_size_sec

    most_common_bed_sec = bed_binned_sec.mode()
    most_common_wake_sec = wake_binned_sec.mode()
    
    most_common_bed = seconds_to_time_str(most_common_bed_sec.iloc[0]) if not most_common_bed_sec.empty else "N/A"
    most_common_wake = seconds_to_time_str(most_common_wake_sec.iloc[0]) if not most_common_wake_sec.empty else "N/A"

    # --- Earliest / Latest times (Using full datetime objects) ---
    # Earliest/Latest Bedtime: Find min/max of the adjusted start date
    earliest_bed_dt = merged_df["start_adj_dt"].min()
    latest_bed_dt = merged_df["start_adj_dt"].max()
    
    # Earliest/Latest Wake Time: Find min/max of the raw end date
    earliest_wake_dt = merged_df["end"].min()
    latest_wake_dt = merged_df["end"].max()


    # --- Best & Worst Month ---
    daily_sleep["Month"] = daily_sleep["Date"].dt.month
    month_avg = daily_sleep.groupby("Month")["Hours_Slept"].mean()

    best_month = month_avg.idxmax()
    worst_month = month_avg.idxmin()

    # --- Sleep Consistency Score ---
    bedtime_std = merged_df["Bed_Seconds_Adjusted"].std() / 3600
    waketime_std = merged_df["Wake_Seconds"].std() / 3600
    consistency_score = bedtime_std + waketime_std

    if consistency_score < 1:
        consistency_label = "Elite consistency"
    elif consistency_score < 2:
        consistency_label = "Pretty good"
    elif consistency_score < 3:
        consistency_label = "Chaotic neutral"
    else:
        consistency_label = "Agent of chaos"

    # --- Awakenings per night ---
    awakenings_per_block = []

    for _, block in merged_df.iterrows():
        start = block["start"]
        end = block["end"]

        # Count original raw intervals inside this *merged block*
        raw_segments = df[
            (df["startDate"] >= start) &
            (df["endDate"] <= end)
        ].sort_values("startDate")

        # The number of awakenings is (number of raw segments - 1)
        # This assumes each segment is separated by an 'Awake' interval
        awakenings = max(0, len(raw_segments) - 1) 
        awakenings_per_block.append(awakenings)

    avg_awakenings = float(np.mean(awakenings_per_block)) if awakenings_per_block else 0
    max_awakenings = int(np.max(awakenings_per_block)) if awakenings_per_block else 0

    # --- Arrays for plotting ---
    sleep_hours_over_year = daily_sleep["Hours_Slept"].tolist()
    bedtime_over_year = merged_df["Bed_Seconds_Adjusted"].tolist()
    waketime_over_year = merged_df["Wake_Seconds"].tolist()

    # === OUTPUT ===
    print("\n## 📊 Sleep Analysis Results for", year)
    print("---")

    print("### ⏳ Total and Average Sleep")
    print(f"* Total Hours Slept: {total_hours:.2f}")
    print(f"* Total Days with Data: {total_days}")
    print(f"* Average Sleep per Day: {avg_sleep:.2f}h")

    print("\n### 💤 Longest & Shortest Sleep")
    print(f"* Longest: {longest['Date'].date()} — {longest['Hours_Slept']:.2f}h")
    print(f"* Shortest: {shortest['Date'].date()} — {shortest['Hours_Slept']:.2f}h")
    
    print("\n### 📏 Sleep Consistency")
    print(f"* Bedtime Std Dev: {bedtime_std:.2f}h")
    print(f"* Waketime Std Dev: {waketime_std:.2f}h")
    print(f"* Sleep Consistency Score: **{consistency_score:.2f}h** → {consistency_label}")

    print("\n### 🕒 Bedtime & Wake Time (MODE - Binned to 15 min)")
    print(f"* Most Common Bedtime: **{most_common_bed}**")
    print(f"* Most Common Wake Time: **{most_common_wake}**")

    print("\n### 🕰 Earliest & Latest Times (Using full Date Context)")
    print(f"* Earliest Bedtime: {earliest_bed_dt.strftime('%I:%M %p')}")
    print(f"* Latest Bedtime: {latest_bed_dt.strftime('%I:%M %p')}")
    print(f"* Earliest Wake Time: {earliest_wake_dt.strftime('%I:%M %p')}")
    print(f"* Latest Wake Time: {latest_wake_dt.strftime('%I:%M %p')}")

    print("\n### 📅 Monthly Sleep Performance")
    print(f"* Best Month: {best_month} — {month_avg[best_month]:.2f}h")
    print(f"* Worst Month: {worst_month} — {month_avg[worst_month]:.2f}h")

    print("\n### 😵 Middle-of-the-Night Awakenings")
    print(f"* Average Awakenings/Night: {avg_awakenings:.2f}")
    print(f"* Max Awakenings in a Night: {max_awakenings}")

    print("\n### 📈 Arrays for Plotting (In Seconds)")
    print(f"sleep_hours_over_year → {len(sleep_hours_over_year)} values")
    print(f"bedtime_over_year → {len(bedtime_over_year)} values")
    print(f"waketime_over_year → {len(waketime_over_year)} values")


# Run
analyze_sleep_data(XML_FILE_PATH, TARGET_YEAR)