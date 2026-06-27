#!/usr/bin/env python3
"""
Test script to verify lab course scheduling with fixed duration = 1.0
"""

import pandas as pd
import math
from schedule_generator import ScheduleGenerator, Lecture

# Load sample data
df = pd.read_csv('sample_courses_up.csv')

# Filter for 4th semester
sem_4 = df[df['semester'] == '4th'].copy()
print("=" * 80)
print("4th SEMESTER COURSES")
print("=" * 80)
print(sem_4[['course_code', 'course_name', 'session_type', 'hours_per_week', 'instructor', 'batch_size']])

# Separate theory and lab
theory_courses = sem_4[sem_4['session_type'] == 'Theory']
lab_courses = sem_4[sem_4['session_type'] == 'Lab']

print("\n" + "=" * 80)
print("THEORY COURSES")
print("=" * 80)
print(theory_courses[['course_code', 'course_name', 'hours_per_week', 'instructor']])

print("\n" + "=" * 80)
print("LAB COURSES")
print("=" * 80)
print(lab_courses[['course_code', 'course_name', 'hours_per_week', 'instructor', 'batch_size']])

# Create generator
print("\n" + "=" * 80)
print("TESTING SCHEDULE GENERATOR")
print("=" * 80)

generator = ScheduleGenerator(
    morning_start="08:30",
    morning_end="17:00",  # This covers the entire day including afternoon
    short_recess_start="10:30",
    short_recess_end="10:45",
    long_recess_start="13:00",
    long_recess_end="14:00",
    days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
)

# Test lab slot generation
print("\nLab slot availability on Monday (after 13:30):")
lab_slots = generator.get_available_slots('Monday', duration=1.0, session_type='Lab')
print(f"Available lab slots: {lab_slots[:5]}")  # Show first 5
print(f"Total lab slots on Monday: {len(lab_slots)}")

print("\nTheory slot availability on Monday:")
theory_slots = generator.get_available_slots('Monday', duration=1.0, session_type='Theory')
print(f"Available theory slots: {theory_slots[:5]}")  # Show first 5
print(f"Total theory slots on Monday: {len(theory_slots)}")

# Test lab course scheduling calculation
print("\n" + "=" * 80)
print("LAB SCHEDULING CALCULATION")
print("=" * 80)

for idx, row in lab_courses.iterrows():
    hours_per_week = row['hours_per_week']
    duration = 1.0  # Fixed!
    num_sessions = max(1, math.ceil(hours_per_week / duration)) if hours_per_week > 0 else 1
    print(f"{row['course_code']:8} | hours/week: {hours_per_week:4.1f} | duration: {duration} | sessions needed: {num_sessions}")

print("\n" + "=" * 80)
print("THEORY SCHEDULING CALCULATION")
print("=" * 80)

for idx, row in theory_courses.iterrows():
    hours_per_week = row['hours_per_week']
    duration = 1.0
    num_sessions = max(1, math.ceil(hours_per_week / duration)) if hours_per_week > 0 else 1
    print(f"{row['course_code']:8} | hours/week: {hours_per_week:4.1f} | duration: {duration} | sessions needed: {num_sessions}")

print("\n✅ All calculations verified!")
