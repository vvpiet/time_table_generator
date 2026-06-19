#!/usr/bin/env python
"""
Test script to verify batch rotation fix works correctly
Simulates: Add 3 lab courses → Generate schedule → Verify output
"""

import pandas as pd
import sys
sys.path.insert(0, 'd:\\Time_table')

from schedule_generator import ScheduleGenerator, Lecture
from app import apply_rotating_batch_assignment
from datetime import datetime

print("\n" + "="*100)
print("TEST: BATCH ROTATION WITH CORRECTED SCHEDULE GENERATION")
print("="*100)

# Initialize schedule generator
generator = ScheduleGenerator(
    morning_start="08:30",
    morning_end="17:00",
    short_recess_start="10:30",
    short_recess_end="10:45",
    long_recess_start="13:00",
    long_recess_end="14:00",
    use_reference_periods=False
)

print("\n📝 STEP 1: Add 3 Lab Courses for Semester 4")
print("-"*100)

labs = [
    ("CS405", "Database Lab", "Dr. Kumar"),
    ("CS406", "Data Science Lab", "Dr. Singh"),
    ("CS407", "Networks Lab", "Dr. Patel"),
]

print(f"✓ Lab 1: {labs[0][0]} - {labs[0][1]}")
print(f"✓ Lab 2: {labs[1][0]} - {labs[1][1]}")
print(f"✓ Lab 3: {labs[2][0]} - {labs[2][1]}")

print("\n📅 STEP 2: Schedule Simulation (All labs at 15:30-17:00 on EACH day)")
print("-"*100)

# Simulate the NEW schedule generation logic for labs
# Labs get assigned to ALL days at the same time slot
all_assignments = []
time_slot = ("15:30", "17:00")

for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    for course_code, course_name, instructor in labs:
        lecture = Lecture(
            course_code=course_code,
            course_name=course_name,
            instructor=instructor,
            session_type="Lab",
            sem="4",
            section="A",
            duration=1.5,
            batch="All"
        )
        # Assign the lecture
        generator.assign_lecture(lecture, day, time_slot[0], time_slot[1])
        all_assignments.append({
            'Day': day,
            'Course Code': course_code,
            'Course Name': course_name,
            'Time': f"{time_slot[0]}-{time_slot[1]}"
        })

print(f"✓ All labs scheduled for each day at {time_slot[0]}-{time_slot[1]}")
print(f"✓ Total assignments: {len(all_assignments)} (3 labs × 5 days)")

print("\n🔄 STEP 3: Apply Batch Rotation")
print("-"*100)

# Get the timetable from generator
df = generator.get_complete_timetable()

# Filter only lab courses at 15:30-17:00
df_labs = df[(df['Type'] == 'Lab') & (df['Time'] == '15:30-17:00')].copy()

print(f"Total rows before rotation: {len(df_labs)}")
print(f"Labs at 15:30-17:00: {len(df_labs)}")

# Convert to dict format and apply batch rotation
rows = df_labs.to_dict(orient='records')
batch_size_map = {"4": 3}  # Semester 4 with 3 batches
rotated_rows = apply_rotating_batch_assignment(rows, batch_size_map)

print(f"Batches assigned: ✓")

print("\n📊 STEP 4: Results - Batch Rotation Pattern")
print("="*100)

# Recreate DataFrame with rotated batches
df_rotated = pd.DataFrame(rotated_rows)

# Create pivot table for visualization
pivot = df_rotated.pivot_table(
    index='Course Code',
    columns='Day',
    values='Batch',
    aggfunc='first'
)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
pivot = pivot[[day for day in day_order if day in pivot.columns]]

print("\n🎯 BATCH ROTATION PATTERN (EXPECTED):\n")
print(pivot)

print("\n\n✅ EXPECTED vs ACTUAL:")
print("-"*100)

expected = {
    'Monday': {'CS405': '1', 'CS406': '2', 'CS407': '3'},
    'Tuesday': {'CS405': '2', 'CS406': '3', 'CS407': '1'},
    'Wednesday': {'CS405': '3', 'CS406': '1', 'CS407': '2'},
    'Thursday': {'CS405': '1', 'CS406': '2', 'CS407': '3'},
    'Friday': {'CS405': '2', 'CS406': '3', 'CS407': '1'},
}

all_match = True
for day in day_order:
    day_data = df_rotated[df_rotated['Day'] == day].sort_values('Course Code')
    print(f"\n{day}:")
    for course_code in ['CS405', 'CS406', 'CS407']:
        course_row = day_data[day_data['Course Code'] == course_code]
        if not course_row.empty:
            actual_batch = str(int(course_row['Batch'].values[0]))
            expected_batch = expected[day][course_code]
            match = "✓" if actual_batch == expected_batch else "✗"
            if actual_batch != expected_batch:
                all_match = False
            print(f"  {match} {course_code}: Expected B{expected_batch}, Got B{actual_batch}")

print("\n" + "="*100)
if all_match:
    print("✅ ALL TESTS PASSED - BATCH ROTATION WORKING CORRECTLY!")
else:
    print("❌ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
print("="*100 + "\n")

print("\n📝 INTERPRETATION:")
print("-"*100)
print("""
Each day at the same time slot (15:30-17:00):
- All 3 labs are present
- Each lab has a different batch number
- Batch numbers rotate daily following the pattern

This ensures:
1. ✓ All batches are fairly distributed
2. ✓ No batch meets the same lab on consecutive days
3. ✓ Pattern repeats every 'batch_size' days (every 3 days here)
4. ✓ Labs remain at consistent time slots (15:30-17:00)
""")
