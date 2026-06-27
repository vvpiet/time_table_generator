#!/usr/bin/env python3
"""
Comprehensive test to verify lab and theory course scheduling
with fixed duration calculation and proper time configuration
"""

import pandas as pd
import math
from schedule_generator import ScheduleGenerator, Lecture
from datetime import datetime, time

# Load sample data
df = pd.read_csv('sample_courses_up.csv')

# Initialize generator with correct times
generator = ScheduleGenerator(
    morning_start="08:30",
    morning_end="17:00",  # Covers full day including afternoon
    short_recess_start="10:30",
    short_recess_end="10:45",
    long_recess_start="13:00",
    long_recess_end="14:00",
    days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
)

# Process 4th semester
print("=" * 80)
print("SCHEDULING 4th SEMESTER")
print("=" * 80)

sem_4 = df[df['semester'] == '4th'].copy()
theory_courses = sem_4[sem_4['session_type'] == 'Theory'].reset_index(drop=True)
lab_courses = sem_4[sem_4['session_type'] == 'Lab'].reset_index(drop=True)

print(f"\n✓ Theory courses to schedule: {len(theory_courses)}")
for idx, row in theory_courses.iterrows():
    print(f"  {row['course_code']:8} - {row['course_name']:15} - {row['hours_per_week']:3.1f} hr/week")

print(f"\n✓ Lab courses to schedule: {len(lab_courses)}")
for idx, row in lab_courses.iterrows():
    print(f"  {row['course_code']:8} - {row['course_name']:15} - {row['hours_per_week']:3.1f} hr/week")

# Try to schedule labs
print("\n" + "-" * 80)
print("SCHEDULING LAB COURSES")
print("-" * 80)

scheduled_labs = 0
failed_labs = []

for idx, row in lab_courses.iterrows():
    course_code = row['course_code']
    duration = 1.0  # All courses now use 1-hour sessions
    hours_per_week = row['hours_per_week']
    num_sessions = max(1, math.ceil(hours_per_week / duration)) if hours_per_week > 0 else 1
    
    sessions_scheduled = 0
    scheduled_days = []
    
    for day in generator.days:
        if sessions_scheduled >= num_sessions:
            break
        
        lab_slots = generator.get_available_slots(day, duration=duration, session_type='Lab')
        if lab_slots:
            slot = lab_slots[0]
            scheduled_days.append(day)
            sessions_scheduled += 1
            
            # Create lecture and assign
            lecture = Lecture(
                course_code=course_code,
                course_name=row['course_name'],
                instructor=row['instructor'],
                session_type='Lab',
                sem='4th',
                section=row['section'],
                branch=row['branch'],
                duration=duration,
                batch=f"1-{int(row['batch_size'])}" if pd.notna(row['batch_size']) else "All",
                hours_per_week=hours_per_week
            )
            generator.assign_lecture(lecture, day, slot[0], slot[1])
    
    if sessions_scheduled == num_sessions:
        scheduled_labs += 1
        print(f"✅ {course_code:8} - Scheduled {sessions_scheduled} session(s) on {', '.join(scheduled_days)}")
    else:
        failed_labs.append(course_code)
        print(f"❌ {course_code:8} - Only {sessions_scheduled}/{num_sessions} session(s) scheduled")

print(f"\n📊 Lab Scheduling Summary:")
print(f"  Total labs: {len(lab_courses)}")
print(f"  Successfully scheduled: {scheduled_labs}")
print(f"  Failed: {len(failed_labs)}")
if failed_labs:
    print(f"  Failed courses: {', '.join(failed_labs)}")

# Try to schedule theories
print("\n" + "-" * 80)
print("SCHEDULING THEORY COURSES")
print("-" * 80)

scheduled_theories = 0
failed_theories = []

# Sort by sessions needed (descending)
theory_courses_sorted = theory_courses.sort_values(
    by='hours_per_week',
    key=lambda x: x.apply(lambda h: max(1, math.ceil(h / 1.0)) if h > 0 else 1),
    ascending=False
)

for idx, row in theory_courses_sorted.iterrows():
    course_code = row['course_code']
    duration = 1.0
    hours_per_week = row['hours_per_week']
    num_sessions = max(1, math.ceil(hours_per_week / duration)) if hours_per_week > 0 else 1
    
    sessions_scheduled = 0
    scheduled_days = []
    
    for day in generator.days:
        if sessions_scheduled >= num_sessions:
            break
        
        theory_slots = generator.get_available_slots(day, duration=duration, session_type='Theory')
        if theory_slots:
            # Try each available slot
            for slot in theory_slots:
                if sessions_scheduled >= num_sessions:
                    break
                    
                lecture = Lecture(
                    course_code=course_code,
                    course_name=row['course_name'],
                    instructor=row['instructor'],
                    session_type='Theory',
                    sem='4th',
                    section=row['section'],
                    branch=row['branch'],
                    duration=duration,
                    batch="All",
                    hours_per_week=hours_per_week
                )
                
                if not generator._has_overlap(day, 
                                             datetime.strptime(slot[0], "%H:%M"),
                                             datetime.strptime(slot[1], "%H:%M"),
                                             lecture=lecture):
                    generator.assign_lecture(lecture, day, slot[0], slot[1])
                    scheduled_days.append(day)
                    sessions_scheduled += 1
    
    if sessions_scheduled == num_sessions:
        scheduled_theories += 1
        print(f"✅ {course_code:8} - {num_sessions} session(s) on {', '.join(scheduled_days[:2])}{'...' if len(scheduled_days) > 2 else ''}")
    else:
        failed_theories.append(course_code)
        print(f"❌ {course_code:8} - Only {sessions_scheduled}/{num_sessions} session(s) scheduled")

print(f"\n📊 Theory Scheduling Summary:")
print(f"  Total theories: {len(theory_courses)}")
print(f"  Successfully scheduled: {scheduled_theories}")
print(f"  Failed: {len(failed_theories)}")
if failed_theories:
    print(f"  Failed courses: {', '.join(failed_theories)}")

print("\n" + "=" * 80)
print("OVERALL SCHEDULING STATUS FOR 4th SEMESTER")
print("=" * 80)
print(f"Total courses: {len(sem_4)}")
print(f"Total scheduled: {scheduled_labs + scheduled_theories}")
print(f"Success rate: {(scheduled_labs + scheduled_theories) / len(sem_4) * 100:.1f}%")

if scheduled_labs > 0:
    print(f"\n✅ LAB COURSES ARE NOW BEING SCHEDULED!")
if len(failed_theories) == 0 and len(failed_labs) == 0:
    print(f"\n🎉 ALL COURSES SUCCESSFULLY SCHEDULED!")
else:
    print(f"\n⚠️  Some courses failed to schedule. Check capacity and timing.")
