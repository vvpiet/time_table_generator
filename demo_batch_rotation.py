#!/usr/bin/env python
"""Demo of batch rotation transformation for labs at same time"""

import pandas as pd
import sys

# Add current directory to path to import app functions
sys.path.insert(0, 'd:\\Time_table')
from app import apply_rotating_batch_assignment

# Create sample data - 3 lab courses scheduled at 16:00-17:30 across 5 days
# Initially all with batch=1 (before rotation)
sample_data = [
    # Monday
    {'Day': 'Monday', 'Course Code': 'CS405', 'Course Name': 'Database Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Kumar'},
    {'Day': 'Monday', 'Course Code': 'CS406', 'Course Name': 'Data Science Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Singh'},
    {'Day': 'Monday', 'Course Code': 'CS407', 'Course Name': 'Networks Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Patel'},
    # Tuesday
    {'Day': 'Tuesday', 'Course Code': 'CS405', 'Course Name': 'Database Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Kumar'},
    {'Day': 'Tuesday', 'Course Code': 'CS406', 'Course Name': 'Data Science Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Singh'},
    {'Day': 'Tuesday', 'Course Code': 'CS407', 'Course Name': 'Networks Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Patel'},
    # Wednesday
    {'Day': 'Wednesday', 'Course Code': 'CS405', 'Course Name': 'Database Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Kumar'},
    {'Day': 'Wednesday', 'Course Code': 'CS406', 'Course Name': 'Data Science Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Singh'},
    {'Day': 'Wednesday', 'Course Code': 'CS407', 'Course Name': 'Networks Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Patel'},
    # Thursday
    {'Day': 'Thursday', 'Course Code': 'CS405', 'Course Name': 'Database Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Kumar'},
    {'Day': 'Thursday', 'Course Code': 'CS406', 'Course Name': 'Data Science Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Singh'},
    {'Day': 'Thursday', 'Course Code': 'CS407', 'Course Name': 'Networks Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Patel'},
    # Friday
    {'Day': 'Friday', 'Course Code': 'CS405', 'Course Name': 'Database Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Kumar'},
    {'Day': 'Friday', 'Course Code': 'CS406', 'Course Name': 'Data Science Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Singh'},
    {'Day': 'Friday', 'Course Code': 'CS407', 'Course Name': 'Networks Lab', 'Type': 'Lab', 'Time': '16:00-17:30', 'Semester': 3, 'Batch': '1', 'Instructor': 'Dr. Patel'},
]

# Apply batch rotation
batch_size_map = {3: 3}  # Semester 3 has 3 batches
rotated_rows = apply_rotating_batch_assignment(sample_data, batch_size_map)

print("\n" + "="*90)
print("BATCH ROTATION DEMONSTRATION - 3 Labs at Same Time Slot (16:00-17:30)")
print("="*90)

print("\nBEFORE ROTATION (All batches assigned as 1):")
print("-"*90)
df_before = pd.DataFrame(sample_data)
# Show sorted by day and course
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    print(f"\n{day}:")
    day_data = df_before[df_before['Day'] == day].sort_values('Course Code')
    for idx, row in day_data.iterrows():
        print(f"  {row['Course Code']:8} - {row['Course Name']:20} - Batch {row['Batch']}")

print("\n" + "="*90)
print("AFTER ROTATION (Using Fixed Course Order with Daily Cycling):")
print("-"*90)
df_after = pd.DataFrame(rotated_rows)
# Show sorted by day and course
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    print(f"\n{day}:")
    day_data = df_after[df_after['Day'] == day].sort_values('Course Code')
    for idx, row in day_data.iterrows():
        print(f"  {row['Course Code']:8} - {row['Course Name']:20} - Batch {row['Batch']}")

print("\n" + "="*90)
print("TABLE VIEW - Rotation Pattern:")
print("="*90)

# Create a pivot table for easier visualization
pivot_df = df_after.pivot_table(
    index='Course Code',
    columns='Day',
    values='Batch',
    aggfunc='first'
)
# Reorder columns by day
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
pivot_df = pivot_df[[day for day in day_order if day in pivot_df.columns]]
print("\n", pivot_df)

print("\n" + "="*90)
print("✅ EXPLANATION:")
print("="*90)
print("""
The batch rotation works with a fixed course order and daily cycling:

Course Order (Global): CS405 (index 0) → CS406 (index 1) → CS407 (index 2)
Batch Size: 3

Formula: batch_number = ((course_index + day_offset) % batch_size) + 1

Where day_offset = 0 (Monday), 1 (Tuesday), 2 (Wednesday), etc.

Examples:
- Monday (offset=0): CS405→(0+0)%3+1=1, CS406→(1+0)%3+1=2, CS407→(2+0)%3+1=3
- Tuesday (offset=1): CS405→(0+1)%3+1=2, CS406→(1+1)%3+1=3, CS407→(2+1)%3+1=1  
- Wednesday (offset=2): CS405→(0+2)%3+1=3, CS406→(1+2)%3+1=1, CS407→(2+2)%3+1=2
- Thursday (offset=3): Same as Monday (3%3=0)
- Friday (offset=4): Same as Tuesday (4%3=1)

This ensures that:
1. Each day at the same time slot has all 3 labs (with different batches)
2. Batches rotate daily - no batch meets the same lab on consecutive days
3. Pattern repeats every `batch_size` days
""")
print("="*90 + "\n")
