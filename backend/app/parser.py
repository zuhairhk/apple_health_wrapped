import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
import numpy as np

# --- Configuration ---
FILE_PATH = "export.xml"
WRAPPED_YEAR = 2025

# --- Utility Functions ---

def parse_date(dt: str):
    """Parses date string safely."""
    try:
        # Handles Apple Health's optional 'Z' and Timezone format
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None

def determine_sleep_day(end_date):
    """Defines the 'Sleep Day' as the calendar date the sleep period ended."""
    return end_date.strftime('%Y-%m-%d')

def time_to_seconds_of_day(dt_obj):
    """Converts a datetime object to seconds since midnight, adjusted for bedtime."""
    seconds = dt_obj.hour * 3600 + dt_obj.minute * 60 + dt_obj.second
    # Shift time forward 24 hours if it is before noon (for proper averaging of times across midnight)
    if dt_obj.hour < 12: 
        seconds += 86400
    return seconds

def seconds_to_time_str(seconds):
    """Converts adjusted seconds back to a HH:MM:SS time string."""
    # Modulo 86400 ensures the time is within a 24-hour day cycle
    return (datetime.min + timedelta(seconds=int(seconds) % 86400)).strftime('%I:%M %p')

# ----------------------------------------------------------------------------
# CORE WRAPPED FUNCTION
# ----------------------------------------------------------------------------

def get_wrapped_stats():
    # --- Data Containers ---
    steps_total = 0
    steps_monthly = defaultdict(int)

    distance_total_km = 0.0
    distance_monthly_km = defaultdict(float)
    distance_record_count = 0
    distance_by_unit = defaultdict(float)

    flights_total = 0

    # SLEEP: Store all raw sleep analysis segments (Core, REM, Awake, Deep) for consolidation
    raw_sleep_segments = [] 
    sleep_monthly_hours = defaultdict(float) # Net sleep hours per month

    # HR
    resting_hr_values = []
    workout_hr_values = []

    # WORKOUTS
    workouts = []
    workouts_monthly = defaultdict(int)  # Count of workouts per month
    workouts_daily_calories = defaultdict(float)  # Calories burned per day
    total_runs = 0
    run_distances = []
    run_paces = []
    longest_run_km = 0.0
    fastest_pace = None
    # calories per workout (kcal)
    # will be filled when parsing WorkoutStatistics
    # each workout dict may get a 'calories_kcal' key

    # RINGS (Placeholders)
    move_total = 0.0
    exercise_total = 0.0
    stand_total = 0.0
    
    # --- PASS 1 — Workouts (to be associated with HR data later) ---
    for event, elem in ET.iterparse(FILE_PATH, events=("start", "end")):
        if elem.tag == "Workout" and event == "start":
            wtype = elem.attrib.get("workoutActivityType", "")
            start_dt = parse_date(elem.attrib.get("startDate", ""))
            end_dt = parse_date(elem.attrib.get("endDate", ""))

            if not start_dt or start_dt.year != WRAPPED_YEAR:
                elem.clear()
                continue

            duration_min = float(elem.attrib.get("duration", 0) or 0)
            duration_sec = duration_min * 60.0

            workout = {
                "type": wtype,
                "start": start_dt,
                "end": end_dt,
                "distance_km": 0.0,
                "duration_sec": duration_sec,
            }

            for child in list(elem):
                if child.tag == "WorkoutStatistics":
                    qtype = child.attrib.get("type", "")
                    if "DistanceWalkingRunning" in qtype:
                        raw = float(child.attrib.get("sum", 0) or 0)
                        unit = child.attrib.get("unit", "").lower()
                        
                        km = raw # Assume km unless otherwise specified
                        if unit == "m":
                            km = raw / 1000
                        elif unit == "mi":
                            km = raw * 1.60934
                            
                        workout["distance_km"] = km
                    # Attempt to capture workout energy (calories)
                    if "energy" in qtype.lower() or "activeenergy" in qtype.lower() or "energyburned" in qtype.lower():
                        try:
                            raw_energy = float(child.attrib.get("sum", 0) or 0)
                            unit_e = child.attrib.get("unit", "").lower()
                            kcal = raw_energy
                            if unit_e and "kcal" in unit_e:
                                kcal = raw_energy
                            elif unit_e and ("kj" in unit_e):
                                # kJ -> kcal (1 kcal = 4.184 kJ)
                                kcal = raw_energy / 4.184
                            elif unit_e and ("j" in unit_e):
                                # J -> kcal
                                kcal = raw_energy / 4184.0
                            else:
                                # Unknown unit: assume kcal
                                kcal = raw_energy
                            workout["calories_kcal"] = kcal
                        except Exception:
                            pass

                child.clear()
            workouts.append(workout)
            # Track monthly workout count
            workouts_monthly[start_dt.month] += 1
            # Track daily calories burned
            workout_date_str = start_dt.strftime('%Y-%m-%d')
            if "calories_kcal" in workout:
                workouts_daily_calories[workout_date_str] += workout["calories_kcal"]

        elem.clear()
    
    # --- PASS 2 — Records (Sleep, HR, steps, distance, etc.) ---
    # Re-read or rewind the file iterator for Pass 2
    for event, elem in ET.iterparse(FILE_PATH, events=("start", "end")):
        if elem.tag == "Record" and event == "start":
            rtype = elem.attrib.get("type", "")
            value = elem.attrib.get("value", "")
            start_dt = parse_date(elem.attrib.get("startDate", ""))
            end_dt = parse_date(elem.attrib.get("endDate", ""))

            if not start_dt or not end_dt:
                elem.clear()
                continue
            
            # Skip if record doesn't fall in or touch the WRAPPED_YEAR
            if not (start_dt.year == WRAPPED_YEAR or end_dt.year == WRAPPED_YEAR):
                elem.clear()
                continue
            
            # ---------- STEPS ----------
            if rtype == "HKQuantityTypeIdentifierStepCount":
                if start_dt.year == WRAPPED_YEAR:
                    v = int(float(value))
                    steps_total += v
                    steps_monthly[start_dt.month] += v

            # ---------- DISTANCE ----------
            if rtype == "HKQuantityTypeIdentifierDistanceWalkingRunning":
                if start_dt.year == WRAPPED_YEAR:
                    raw = float(value)
                    unit = elem.attrib.get("unit", "").lower()

                    km = raw # Assume km unless otherwise specified
                    if unit in ["m", "meter", "meters"]:
                        km = raw / 1000.0
                    elif unit in ["mi", "mile", "miles"]:
                        km = raw * 1.60934

                    distance_total_km += km
                    distance_monthly_km[start_dt.month] += km
                    distance_record_count += 1
                    distance_by_unit[unit or "unknown"] += raw

            # ---------- FLIGHTS ----------
            if rtype == "HKQuantityTypeIdentifierFlightsClimbed":
                if start_dt.year == WRAPPED_YEAR:
                    flights_total += int(float(value))

            # ---------- STAND HOURS ----------
            if rtype == "HKCategoryTypeIdentifierAppleStandHour":
                if start_dt.year == WRAPPED_YEAR:
                    if "Stood" in value:
                        stand_total += 1

            # ---------- RESTING HR ----------
            if rtype == "HKQuantityTypeIdentifierRestingHeartRate":
                if start_dt.year == WRAPPED_YEAR:
                    resting_hr_values.append(float(value))

            # ---------- SLEEP (Collect all raw segments) ----------
            if rtype == "HKCategoryTypeIdentifierSleepAnalysis":
                category = elem.attrib.get("value", "")
                
                # Only real sleep categories (Asleep/Awake), not "InBed"
                if "Asleep" in category or "Awake" in category: 
                    raw_sleep_segments.append({
                        'start': start_dt, 
                        'end': end_dt, 
                        'value': category
                    })
                    # Calculate net time slept for monthly aggregation
                    if 'Asleep' in category:
                        sleep_monthly_hours[start_dt.month] += (end_dt - start_dt).total_seconds() / 3600.0

            # ---------- HR DURING WORKOUT ----------
            if rtype == "HKQuantityTypeIdentifierHeartRate":
                hr = float(value)
                if start_dt:
                    for w in workouts:
                        if w["start"] <= start_dt <= w["end"]:
                            workout_hr_values.append(hr)
                            break

            elem.clear()
    
    # ----------------------------------------------------------------------------
    # CONSOLIDATED SLEEP ANALYSIS
    # ----------------------------------------------------------------------------
    
    sleep_results = {}
    
    if raw_sleep_segments:
        df = pd.DataFrame(raw_sleep_segments)
        df = df.sort_values("end").reset_index(drop=True)
        
        # Consolidation Logic: New period starts if gap > 6 hours
        MAX_INTERRUPTION_HOURS = 6.0 
        df['Time_Since_Last'] = (df['start'] - df['end'].shift(1)).dt.total_seconds() / 3600
        df['Is_New_Period'] = (df['Time_Since_Last'].fillna(MAX_INTERRUPTION_HOURS + 0.1) > MAX_INTERRUPTION_HOURS)
        df['Period_ID'] = df['Is_New_Period'].cumsum()
        
        grouped_periods = df.groupby('Period_ID')
        
        # Containers for Final Sleep Stats
        consolidated_nights = []
        all_bedtimes_sec = []
        all_waketimes_sec = []
        total_net_sleep_hours = 0.0

        for period_id, group in grouped_periods:
            period_start = group['start'].min()
            period_end = group['end'].max()
            
            # Net sleep duration (sum of Asleep segments)
            net_sleep_duration_sec = group[group['value'].str.contains('Asleep')]['end'].sub(
                group[group['value'].str.contains('Asleep')]['start']
            ).dt.total_seconds().sum()
            
            net_sleep_hours = net_sleep_duration_sec / 3600.0
            total_block_duration_hours = (period_end - period_start).total_seconds() / 3600
            
            # Awakenings (count of Awake segments)
            awake_count = len(group[group['value'].str.contains('Awake', na=False)])
            
            # Compute adjusted seconds for bedtime/waketime and append for final stats
            bedtime_sec = time_to_seconds_of_day(period_start)
            waketime_sec = time_to_seconds_of_day(period_end)

            all_bedtimes_sec.append(bedtime_sec)
            all_waketimes_sec.append(waketime_sec)
            total_net_sleep_hours += net_sleep_hours

            consolidated_nights.append({
                'start': period_start,
                'end': period_end,
                'net_sleep_hours': net_sleep_hours,
                'block_duration_hours': total_block_duration_hours,
                'awake_count': awake_count,
                'bedtime_sec': bedtime_sec,
                'waketime_sec': waketime_sec,
                'date_woke': determine_sleep_day(period_end)
            })

        # --- CALCULATE WRAPPED SLEEP STATS ---
        
        total_nights_with_data = len(consolidated_nights)
        
        # 1. Total & Avg Sleep
        avg_sleep_per_night = total_net_sleep_hours / total_nights_with_data if total_nights_with_data else 0
        
        # 2. Longest/Shortest Night
        longest_night = max(consolidated_nights, key=lambda x: x['net_sleep_hours'])
        shortest_night = min(consolidated_nights, key=lambda x: x['net_sleep_hours'])

        # 3. Most Awakened Night
        most_awake_night = max(consolidated_nights, key=lambda x: x['awake_count'])
        
        # 4. Average Bed/Wake Time (using NumPy mean on adjusted seconds)
        avg_bedtime_sec = np.mean(all_bedtimes_sec) if all_bedtimes_sec else 0
        avg_waketime_sec = np.mean(all_waketimes_sec) if all_waketimes_sec else 0
        
        # 5. Average Sleep Efficiency removed per request
        total_block_hours = sum(n['block_duration_hours'] for n in consolidated_nights)
        
        # Prepare plottable data array for the frontend
        nightly_sleep_data = [{
            'date': n['date_woke'],
            # Convert seconds to decimal hours (needed for the chart's Y-axis scale)
            'bedtime_h_dec': n['bedtime_sec'] / 3600,
            'wake_time_h_dec': n['waketime_sec'] / 3600
        } for n in consolidated_nights]

        sleep_results = {
            "total_net_sleep_hours": round(total_net_sleep_hours, 2),
            "total_nights_with_data": total_nights_with_data,
            "avg_sleep_per_night": round(avg_sleep_per_night, 2),
            "avg_bedtime": seconds_to_time_str(avg_bedtime_sec),
            "avg_waketime": seconds_to_time_str(avg_waketime_sec),
            # Removed: avg_sleep_efficiency and total_deep_sleep_min
            
            "longest_sleep_night": {
                "date_woke": determine_sleep_day(longest_night['end']),
                "duration_hours": round(longest_night['net_sleep_hours'], 2)
            },
            "shortest_sleep_night": {
                "date_woke": determine_sleep_day(shortest_night['end']),
                "duration_hours": round(shortest_night['net_sleep_hours'], 2)
            },
            "most_woken_night": {
                "date_woke": determine_sleep_day(most_awake_night['end']),
                "awakening_count": most_awake_night['awake_count']
            }
        ,
            "nightly_sleep_data": nightly_sleep_data
        }
        
    # --------------------------------------
    # RUNNING ANALYSIS
    # --------------------------------------
    for w in workouts:
        if "Running" not in w["type"]:
            continue

        dist = w["distance_km"]
        dur = w["duration_sec"]

        if dist <= 0 or dur <= 0:
            continue

        total_runs += 1
        run_distances.append(dist)
        longest_run_km = max(longest_run_km, dist)

        pace = (dur / 60.0) / dist
        run_paces.append(pace)
        if fastest_pace is None or pace < fastest_pace:
            fastest_pace = pace
    # -- Workout-level aggregates (all workout types) --
    workouts_count = len(workouts)
    workout_durations_sec = [w.get('duration_sec', 0) for w in workouts if w.get('duration_sec', 0) > 0]
    avg_workout_time_min = (sum(workout_durations_sec) / len(workout_durations_sec) / 60.0) if workout_durations_sec else 0
    total_workout_calories = sum((w.get('calories_kcal', 0) for w in workouts))
    avg_calories_per_workout = (total_workout_calories / workouts_count) if workouts_count else 0
    # Highest/avg BPM during workouts (workout_hr_values collected earlier)
    highest_workout_bpm = max(workout_hr_values) if workout_hr_values else 0
    
    # Find day with most calories burned
    max_calories_day = None
    max_calories_value = 0.0
    if workouts_daily_calories:
        max_calories_day, max_calories_value = max(workouts_daily_calories.items(), key=lambda x: x[1])
            
    # --------------------------------------
    # FINAL METRICS
    # --------------------------------------
    resting_hr_avg = sum(resting_hr_values) / len(resting_hr_values) if resting_hr_values else 0
    workout_hr_avg = sum(workout_hr_values) / len(workout_hr_values) if workout_hr_values else 0

    return {
        "wrapped_year": WRAPPED_YEAR,

        "steps_total": steps_total,
        "steps_monthly": dict(steps_monthly),
        "distance_total_km": round(distance_total_km, 2),
        "flights_total": flights_total,
        
        "resting_hr_avg": round(resting_hr_avg, 1),
        "workout_hr_avg": round(workout_hr_avg, 1),

        # Workout / Fitness aggregates
        "workouts_count": workouts_count,
        "highest_workout_bpm": round(highest_workout_bpm, 1),
        "avg_workout_bpm": round(workout_hr_avg, 1),
        "avg_workout_time_min": round(avg_workout_time_min, 1),
        "avg_calories_per_workout": round(avg_calories_per_workout, 1),
        "total_workout_calories": round(total_workout_calories, 1),
        "most_calories_burned_day": max_calories_day or "N/A",
        "most_calories_burned_value": round(max_calories_value, 1),

        "total_runs": total_runs,
        "longest_run_km": round(longest_run_km, 2),
        "run_distances": [round(d, 2) for d in run_distances],
        "fastest_pace_min_per_km": round(fastest_pace, 2) if fastest_pace else None,

        # FINAL CONSOLIDATED SLEEP METRICS
        **sleep_results,
        "sleep_monthly_hours": sleep_monthly_hours,
        # Workout monthly breakdown
        "workouts_monthly": dict(workouts_monthly),
        # Exercise/stand totals (exercise derived from total workout durations as fallback)
        "exercise_total": round(sum(workout_durations_sec) / 60.0, 1),
        "stand_total": round(stand_total, 1),
    }

# NOTE: No execution or print statements here as requested.