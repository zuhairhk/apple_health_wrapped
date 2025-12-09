import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

# --- Configuration ---
XML_FILE_PATH = 'export.xml'
TARGET_YEAR = 2025
SLEEP_TYPE = 'HKCategoryTypeIdentifierSleepAnalysis'

# --- Utility Function ---

def determine_sleep_day(end_date):
    """
    Defines the 'Sleep Day' as the calendar date the sleep period ended.
    This helps group records spanning midnight into a single night.
    """
    return end_date.strftime('%Y-%m-%d')


def extract_detailed_sleep_periods(file_path, year):
    """
    Parses XML, extracts all sleep analysis records for the target year,
    and groups them into complete night-time periods.
    """
    print(f"Loading data from {file_path}...")

    # Load XML safely
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error loading XML: {e}")
        return

    raw_records = []

    # 1. Extract and Filter Records for Target Year
    for record in root.iter('Record'):
        if record.get('type') == SLEEP_TYPE:
            end_date_str = record.get('endDate')
            
            if end_date_str:
                try:
                    record_date = datetime.strptime(end_date_str.split(" ")[0], "%Y-%m-%d")
                    if record_date.year == year:
                        raw_records.append(record.attrib)
                except ValueError:
                    continue

    if not raw_records:
        print(f"No sleep analysis records found ending in {year}.")
        return

    # 2. Convert to DataFrame and Prepare Dates
    df = pd.DataFrame(raw_records)
    date_format = "%Y-%m-%d %H:%M:%S %z"
    df["startDate"] = pd.to_datetime(df["startDate"], format=date_format)
    df["endDate"] = pd.to_datetime(df["endDate"], format=date_format)
    df["Sleep_Day"] = df["endDate"].apply(determine_sleep_day)
    
    # --- New Consolidation Logic (Allows for long breaks within a night) ---
    
    # Sort the data by the sleep end time
    df_sorted = df.sort_values("endDate").reset_index(drop=True)
    
    # Calculate the time difference between the end of one record and the start of the next
    df_sorted['Time_Since_Last'] = (df_sorted['startDate'] - df_sorted['endDate'].shift(1)).dt.total_seconds() / 3600
    
    # A new sleep period starts if it's the first record, OR if the gap is > 6 hours.
    # Allowing up to 6 hours for breaks (like waking for Fajr and returning to sleep)
    MAX_INTERRUPTION_HOURS = 6.0 
    
    df_sorted['Is_New_Period'] = (df_sorted['Time_Since_Last'].fillna(MAX_INTERRUPTION_HOURS + 0.1) > MAX_INTERRUPTION_HOURS)
    
    # Assign a unique ID to each continuous sleep period
    df_sorted['Period_ID'] = df_sorted['Is_New_Period'].cumsum()
    
    # 4. Aggregate by Period ID and Format Output

    grouped_periods = df_sorted.groupby('Period_ID')

    final_sleep_periods = []
    
    for period_id, group in grouped_periods:
        
        # Determine overall start and end times for the consolidated night
        period_start = group['startDate'].min()
        period_end = group['endDate'].max()
        
        sleep_day = determine_sleep_day(period_end)

        # Calculate total duration by finding the difference between the first start and last end
        total_block_duration_hours = (period_end - period_start).total_seconds() / 3600
        
        # --- New Awakening Counter and Times ---
        awake_events = []
        
        # Filter segments that are classified as 'Awake'
        awake_segments = group[group['value'].str.contains('Awake', na=False)]
        
        # For each awake segment, record the end time (when you finished being awake)
        for _, row in awake_segments.iterrows():
            awake_events.append(row['endDate'].strftime('%I:%M %p'))

        # Structure the detailed records for the segment summary
        detailed_segments = []
        for _, row in group.iterrows():
            duration_sec = (row['endDate'] - row['startDate']).total_seconds()
            detailed_segments.append({
                'value': row['value'],
                'start': row['startDate'].strftime('%Y-%m-%d %H:%M:%S %z'),
                'end': row['endDate'].strftime('%Y-%m-%d %H:%M:%S %z'),
                'duration_min': round(duration_sec / 60, 2)
            })
            
        final_sleep_periods.append({
            'Sleep_Period_Key': f"{period_start.strftime('%m-%d %I:%M %p')} --> {period_end.strftime('%m-%d %I:%M %p')}",
            'Wake_Date': sleep_day,
            'Bed_Time': period_start.strftime('%I:%M %p'),
            'Wake_Time': period_end.strftime('%I:%M %p'),
            'Total_Block_Duration_Hours': round(total_block_duration_hours, 2),
            'Awake_Count': len(awake_events),
            'Awake_Times': awake_events,
            'Segments': detailed_segments
        })
        
    return final_sleep_periods

# --- Execution ---

all_sleep_data = extract_detailed_sleep_periods(XML_FILE_PATH, TARGET_YEAR)

if all_sleep_data:
    print("\n## ✨ Detailed Sleep Periods for 2025")
    print(f"Total Consolidated Sleep Periods Found: **{len(all_sleep_data)}**")
    print("---")
    
    # Output the first 5 sleep periods for review
    print("### 📝 Sample Output (First 5 Sleep Periods):")
    for i, period in enumerate(all_sleep_data[:5]):
        print(f"\n--- 🌙 Consolidated Period {i+1} (Woke up {period['Wake_Date']}) ---")
        print(f"* **Start/End Time:** {period['Bed_Time']} to {period['Wake_Time']}")
        print(f"* **Total Block Duration:** {period['Total_Block_Duration_Hours']} hours")
        print(f"* **Times Woke Up (Awake Segments):** {period['Awake_Count']} times")
        
        if period['Awake_Count'] > 0:
            print(f"  - **Awakening Times:** {', '.join(period['Awake_Times'])}")

        # Aggregate segment types for summary
        summary = {}
        total_time_asleep_min = 0
        
        for seg in period['Segments']:
            sleep_type = seg['value'].split('SleepAnalysis')[-1]
            duration = seg['duration_min']
            summary[sleep_type] = summary.get(sleep_type, 0) + duration
            if 'Asleep' in sleep_type:
                total_time_asleep_min += duration
        
        print(f"* **Total Time Asleep:** {round(total_time_asleep_min / 60, 2)} hours")
        print(f"Segment Summary (Minutes):")
        
        # Sort and print the segment types
        for type, duration in sorted(summary.items(), key=lambda item: item[1], reverse=True):
            print(f"  - **{type}:** {round(duration, 1)} min")