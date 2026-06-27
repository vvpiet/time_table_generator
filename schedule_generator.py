"""
Timetable Generation Module
Handles the core logic for generating non-overlapping schedules
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd

class TimeSlot:
    """Represents a time slot in the timetable"""
    def __init__(self, start_time: str, end_time: str):
        self.start_time = datetime.strptime(start_time, "%H:%M")
        self.end_time = datetime.strptime(end_time, "%H:%M")
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another"""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)
    
    def __str__(self) -> str:
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class Lecture:
    """Represents a lecture or lab session"""
    def __init__(self, course_code: str, course_name: str, instructor: str, 
                 session_type: str, sem: str, section: str, branch: str = "", duration: float = 1.0, batch: str = "All", hours_per_week: float = 0):
        self.course_code = course_code
        self.course_name = course_name
        self.instructor = instructor
        self.session_type = session_type  # "Theory" or "Lab"
        self.sem = sem
        self.section = section
        self.branch = branch
        self.duration = duration  # in hours (1.0 for theory, 1.5 for lab)
        self.batch = batch
        self.hours_per_week = hours_per_week  # Curriculum hours per week
        self.assigned_slot = None
        self.assigned_period = None
        self.day = None
    
    def __repr__(self) -> str:
        return f"{self.course_code} ({self.session_type}) - {self.instructor}"

class ScheduleGenerator:
    """Generates non-overlapping timetable"""
    
    def __init__(self, morning_start: str, morning_end: str, 
                 short_recess_start: str, short_recess_end: str,
                 long_recess_start: str, long_recess_end: str,
                 use_reference_periods: bool = False,
                 days: list = None):
        """
        Initialize the schedule generator
        Times should be in HH:MM format (24-hour)
        """
        self.morning_start = datetime.strptime(morning_start, "%H:%M")
        self.morning_end = datetime.strptime(morning_end, "%H:%M")
        self.short_recess_start = datetime.strptime(short_recess_start, "%H:%M")
        self.short_recess_end = datetime.strptime(short_recess_end, "%H:%M")
        self.long_recess_start = datetime.strptime(long_recess_start, "%H:%M")
        self.long_recess_end = datetime.strptime(long_recess_end, "%H:%M")
        self.use_reference_periods = use_reference_periods
        self.days = days or ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        self.occupied_slots = {day: [] for day in self.days}
        self.timetable = []
        self.period_slots = []
        
        if self.use_reference_periods:
            self._build_reference_periods()

    def _build_reference_periods(self):
        """Build reference periods from configured timing and recess settings."""
        self.period_slots = []
        period_label = 1
        current = self.morning_start

        while current + timedelta(minutes=45) <= self.morning_end:
            # Skip intervals that overlap any recess
            if self._is_in_recess(current, current + timedelta(minutes=45)):
                if current < self.short_recess_end and current + timedelta(minutes=45) > self.short_recess_start:
                    current = self.short_recess_end
                    continue
                if current < self.long_recess_end and current + timedelta(minutes=45) > self.long_recess_start:
                    current = self.long_recess_end
                    continue

            next_end = current + timedelta(hours=1)
            if next_end > self.morning_end:
                next_end = self.morning_end

            # Skip invalid zero-length periods
            if next_end <= current:
                break

            self.period_slots.append({
                'label': f'Period {period_label}',
                'start': current,
                'end': next_end
            })
            period_label += 1
            current = next_end
    
    def get_available_slots(self, day: str, duration: float, session_type: str = 'Theory', lecture: Lecture = None, **kwargs) -> List[Tuple[str, str]]:
        """Get all available time slots for a given duration on a specific day"""
        available_slots = []
        allow_parallel_labs = session_type == 'Lab'
        
        # For lab sessions, scan the afternoon period for available slots
        if session_type == 'Lab':
            lab_slots = []
            # Start scanning from long_recess_end
            current_time = self.long_recess_end
            
            while current_time < self.morning_end:
                slot_end = current_time + timedelta(hours=duration)
                
                # Ensure slot doesn't exceed morning_end
                if slot_end > self.morning_end:
                    break
                
                # Check if slot is in recess
                if self._is_in_recess(current_time, slot_end):
                    current_time += timedelta(minutes=30)
                    continue
                
                # Check for overlaps with allow_parallel_labs
                if not self._has_overlap(day, current_time, slot_end, lecture=lecture, allow_parallel_labs=True):
                    lab_slots.append((current_time.strftime("%H:%M"), slot_end.strftime("%H:%M")))
                
                current_time += timedelta(minutes=30)  # Scan in 30-minute increments
            
            return lab_slots

        if self.use_reference_periods and self.period_slots:
            for slot in self.period_slots:
                start = slot['start']
                end = start + timedelta(hours=duration)
                
                if end > self.morning_end:
                    continue
                if self._is_in_recess(start, end):
                    continue
                if not self._has_overlap(day, start, end, lecture=lecture, allow_parallel_labs=allow_parallel_labs):
                    available_slots.append((start.strftime("%H:%M"), end.strftime("%H:%M")))
            return available_slots
        
        # In flexible mode, scan the day for valid slots using configured morning_start and morning_end times
        current_time = self.morning_start

        while current_time <= self.morning_end:
            slot_end = current_time + timedelta(hours=duration)
            
            # Ensure slot ends within morning_end
            if slot_end > self.morning_end:
                break
            
            # Check if slot falls within any recess period
            if self._is_in_recess(current_time, slot_end):
                # Jump to after the recess period that conflicts with current slot
                if current_time < self.long_recess_end and slot_end > self.long_recess_start:
                    current_time = self.long_recess_end
                elif current_time < self.short_recess_end and slot_end > self.short_recess_start:
                    current_time = self.short_recess_end
                else:
                    current_time += timedelta(minutes=30)
                continue
            
            # Check if slot overlaps with any occupied slot
            if not self._has_overlap(day, current_time, slot_end, allow_parallel_labs=allow_parallel_labs):
                start_str = current_time.strftime("%H:%M")
                end_str = slot_end.strftime("%H:%M")
                available_slots.append((start_str, end_str))
            
            current_time += timedelta(minutes=30)  # Always move in 30-min increments for dense slot generation
        
        return available_slots    
    def _is_in_recess(self, start: datetime, end: datetime) -> bool:
        """Check if time slot is during recess"""
        # Check long recess
        if start < self.long_recess_end and end > self.long_recess_start:
            return True
        # Check short recess
        if start < self.short_recess_end and end > self.short_recess_start:
            return True
        return False
    
    def _has_overlap(self, day: str, start: datetime, end: datetime, lecture: Lecture = None, allow_parallel_labs: bool = False) -> bool:
        """Check if time slot overlaps with occupied slots"""
        for occupied in self.occupied_slots[day]:
            if occupied['start'] < end and occupied['end'] > start:
                occupied_lecture = occupied.get('lecture')
                if allow_parallel_labs and occupied_lecture and occupied_lecture.session_type == 'Lab':
                    if lecture and lecture.session_type == 'Lab':
                        if occupied_lecture.instructor == lecture.instructor:
                            return True
                        continue
                    return True
                return True
        return False
    
    def _get_period_label(self, start: datetime, end: datetime) -> str:
        for slot in self.period_slots:
            if slot['start'] == start and slot['end'] == end:
                return slot['label']
        return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

    def assign_lecture(self, lecture: Lecture, day: str, start_time: str, end_time: str, allow_parallel_labs: bool = False) -> bool:
        """
        Assign a lecture to a time slot
        
        Args:
            allow_parallel_labs: If True, allows multiple labs at same time (different lab spaces).
                                 Still prevents instructor conflicts.
        """
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        
        if allow_parallel_labs and lecture.session_type == 'Lab':
            for occupied in self.occupied_slots[day]:
                if occupied['start'] < end and occupied['end'] > start:
                    occupied_lecture = occupied.get('lecture')
                    if occupied_lecture and occupied_lecture.session_type == 'Lab':
                        if occupied_lecture.instructor == lecture.instructor:
                            return False
                        continue
                    return False
        else:
            if self._has_overlap(day, start, end, lecture=lecture, allow_parallel_labs=allow_parallel_labs):
                return False
        
        self.occupied_slots[day].append({'start': start, 'end': end, 'lecture': lecture})
        lecture.assigned_slot = f"{start_time} - {end_time}"
        lecture.assigned_period = self._get_period_label(start, end) if self.use_reference_periods else None
        lecture.day = day
        self.timetable.append({
            'Day': day,
            'Time': lecture.assigned_slot,
            'Course Code': lecture.course_code,
            'Course Name': lecture.course_name,
            'Branch': lecture.branch,
            'Type': lecture.session_type,
            'Instructor': lecture.instructor,
            'Semester': lecture.sem,
            'Section': lecture.section,
            'Batch': lecture.batch,
            'Hours Per Week': lecture.hours_per_week
        })
        return True
    
    def get_day_timetable(self, day: str) -> pd.DataFrame:
        """Get timetable for a specific day"""
        day_schedule = [row for row in self.timetable if row['Day'] == day]
        return pd.DataFrame(day_schedule)
    
    def get_complete_timetable(self) -> pd.DataFrame:
        """Get complete timetable"""
        return pd.DataFrame(self.timetable)
    
    def get_instructor_schedule(self, instructor: str) -> pd.DataFrame:
        """Get schedule for a specific instructor"""
        schedule = [row for row in self.timetable if row['Instructor'] == instructor]
        return pd.DataFrame(schedule)
    
    def clear_schedule(self):
        """Clear the generated schedule"""
        self.occupied_slots = {day: [] for day in self.days}
        self.timetable = []
