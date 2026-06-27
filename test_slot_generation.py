"""Test script to verify slot generation for all courses"""
from schedule_generator import ScheduleGenerator
from datetime import datetime, time

# Initialize generator with same config as app
config = {
    'morning_start': '08:30',
    'morning_end': '17:00',
    'short_recess_start': '10:30',
    'short_recess_end': '10:45',
    'long_recess_start': '13:00',
    'long_recess_end': '14:00',
    'use_reference_periods': False
}

gen = ScheduleGenerator(**config)

# Test slot generation for different durations
print("=" * 80)
print("THEORY COURSES (1-hour duration)")
print("=" * 80)
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    slots = gen.get_available_slots(day, duration=1.0, session_type='Theory')
    print(f"\n{day}: {len(slots)} slots available")
    if slots:
        print(f"  First 3: {slots[:3]}")
        print(f"  Last 3: {slots[-3:]}")
    else:
        print("  NO SLOTS!")

print("\n" + "=" * 80)
print("LAB COURSES (2-hour duration)")
print("=" * 80)
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    slots = gen.get_available_slots(day, duration=2.0, session_type='Lab')
    print(f"\n{day}: {len(slots)} slots available")
    if slots:
        print(f"  All slots: {slots}")
    else:
        print("  NO SLOTS!")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# For 4th semester (7 theory + 4 labs)
# Theory: 6 courses * 5 hrs/week (mainly) = 30 sessions total
#         But spread across 5 days, so ~6 sessions per day average
# Labs: 4 courses * 4 hrs/week / 2 hrs duration = 2 sessions per course
#       4 courses * 2 sessions = 8 lab sessions total
#       Spread across 5 days, so ~1.6 sessions per day

theory_slots_per_day = len(gen.get_available_slots('Monday', duration=1.0, session_type='Theory'))
lab_slots_per_day = len(gen.get_available_slots('Monday', duration=2.0, session_type='Lab'))

print(f"\nTheory slots per day: {theory_slots_per_day}")
print(f"Lab slots per day (parallel): {lab_slots_per_day}")

if theory_slots_per_day >= 10:
    print("\n✅ Sufficient theory slots to accommodate all courses")
else:
    print(f"\n⚠️ WARNING: May not have enough theory slots! Need ~6/day, have {theory_slots_per_day}/day")

if lab_slots_per_day >= 2:
    print("✅ Sufficient lab slots for parallel labs")
else:
    print(f"⚠️ WARNING: May not have enough lab slots!")
