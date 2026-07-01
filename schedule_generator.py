"""
Timetable Generation Module
Handles the core logic for generating non-overlapping schedules
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd


def normalize_session_type(session_type: str) -> str:
    """Normalize incoming type values to the internal scheduler values."""
    if session_type is None:
        return 'Theory'
    value = str(session_type).strip().lower()
    if value in {'lab', 'laboratory', 'practical', 'practical lab', 'project', 'project work', 'proj'}:
        return 'Lab'
    if value in {'theory', 'lecture', 'lectures', 'theoretical', 'rotation', 'rotational', 'rot', 'rotation type'}:
        return 'Theory'
    return 'Theory' if 'theory' in value else 'Lab' if 'lab' in value or 'project' in value else 'Theory'


# Backward compatibility alias for older import names
normalize_session = normalize_session_type

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
        """Build fixed reference periods for the timetable."""
        self.period_slots = []
        fixed_slots = [
            ('10:00', '11:00'),
            ('11:00', '12:00'),
            ('12:00', '13:00'),
            ('13:45', '14:45'),
            ('14:45', '15:30'),
            ('15:45', '16:45'),
            ('16:45', '17:30')
        ]
        period_label = 1
        for start_str, end_str in fixed_slots:
            start = datetime.strptime(start_str, '%H:%M')
            end = datetime.strptime(end_str, '%H:%M')
            if start < self.morning_start or end > self.morning_end:
                continue
            if self._is_in_recess(start, end):
                continue
            self.period_slots.append({
                'label': f'Period {period_label}',
                'start': start,
                'end': end
            })
            period_label += 1

    def _get_fixed_theory_start_times(self) -> List[str]:
        """Return exact start times for 1-hour theory slots."""
        return ['10:00', '11:00', '12:00', '13:45', '15:45']

    def _get_fixed_lab_start_times(self, lecture: Lecture = None, day: str = None) -> List[str]:
        """Return an ordered pool of exact lab start times for the semester and day."""
        candidates = ['09:00', '11:00', '13:45', '15:45']
        if lecture and getattr(lecture, 'sem', None):
            digits = ''.join([c for c in str(lecture.sem) if c.isdigit()])
            if digits:
                sem_index = (int(digits) - 1) % len(candidates)
                day_offset = self.days.index(day) if day in self.days else 0
                rotation_offset = (sem_index + day_offset) % len(candidates)
                ordered = []
                for offset in range(len(candidates)):
                    candidate = candidates[(rotation_offset + offset) % len(candidates)]
                    if candidate not in ordered:
                        ordered.append(candidate)
                return ordered
        return candidates

    def get_available_slots(self, day: str, duration: float, session_type: str = 'Theory', lecture: Lecture = None, **kwargs) -> List[Tuple[str, str]]:
        """Get all available time slots for a given duration on a specific day"""
        available_slots = []
        allow_parallel_labs = session_type == 'Lab'

        if session_type == 'Lab':
            lab_slots = []
            # Labs always use exact fixed start times so the schedule stays consistent
            # and rotates by semester/day for better fitment and instructor spacing.
            for start_str in self._get_fixed_lab_start_times(lecture, day=day):
                start_time = datetime.strptime(start_str, '%H:%M')
                slot_end = start_time + timedelta(hours=duration)
                if slot_end > self.morning_end:
                    continue
                if self._is_in_recess(start_time, slot_end):
                    continue
                if not self._has_overlap(day, start_time, slot_end, lecture=lecture, allow_parallel_labs=True):
                    lab_slots.append((start_time.strftime('%H:%M'), slot_end.strftime('%H:%M')))
            return lab_slots

        if self.use_reference_periods and self.period_slots:
            for slot in self.period_slots:
                slot_duration = (slot['end'] - slot['start']).total_seconds() / 3600
                if abs(slot_duration - duration) > 0.01:
                    continue
                if self._has_overlap(day, slot['start'], slot['end'], lecture=lecture, allow_parallel_labs=allow_parallel_labs):
                    continue
                available_slots.append((slot['start'].strftime('%H:%M'), slot['end'].strftime('%H:%M')))
            return available_slots

        # In flexible mode, only consider exact configured start times, not intermediate offsets.
        if session_type == 'Lab':
            start_times = self._get_fixed_lab_start_times(lecture, day=day)
        else:
            start_times = self._get_fixed_theory_start_times()

        for start_str in start_times:
            current_time = datetime.strptime(start_str, '%H:%M')
            slot_end = current_time + timedelta(hours=duration)
            if slot_end > self.morning_end:
                continue
            if self._is_in_recess(current_time, slot_end):
                continue
            if not self._has_overlap(day, current_time, slot_end, lecture=lecture, allow_parallel_labs=allow_parallel_labs):
                available_slots.append((current_time.strftime('%H:%M'), slot_end.strftime('%H:%M')))

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
        """Check if time slot overlaps with occupied slots, checking instructor, batch and section conflicts."""
        for occupied in self.occupied_slots[day]:
            if occupied['start'] < end and occupied['end'] > start:
                occupied_lecture = occupied.get('lecture')

                if not occupied_lecture or not lecture:
                    return True

                # Lab parallelism is allowed only when both are labs, taught by different instructors,
                # and they are not assigned to the same section/batch.
                if allow_parallel_labs and occupied_lecture.session_type == 'Lab' and lecture.session_type == 'Lab':
                    if occupied_lecture.instructor == lecture.instructor:
                        return True
                    if occupied_lecture.section and lecture.section and occupied_lecture.section == lecture.section:
                        return True
                    if lecture.batch != 'All' and occupied_lecture.batch != 'All' and lecture.batch == occupied_lecture.batch:
                        return True
                    continue

                # Any overlap with a different instructor, same batch or same section is a conflict.
                if occupied_lecture.instructor == lecture.instructor:
                    return True
                if occupied_lecture.section and lecture.section and occupied_lecture.section == lecture.section:
                    return True
                if lecture.batch != 'All' and occupied_lecture.batch != 'All' and lecture.batch == occupied_lecture.batch:
                    return True

                return True
        return False
    
    def _get_period_label(self, start: datetime, end: datetime) -> str:
        for slot in self.period_slots:
            if slot['start'] == start and slot['end'] == end:
                return slot['label']
        return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

    def assign_lecture(self, lecture: Lecture, day: str, start_time: str, end_time: str, allow_parallel_labs: bool = False, allow_theory_afternoon: bool = False, existing_lectures: List[Lecture] = None) -> bool:
        """
        Assign a lecture to a time slot
        
        Args:
            allow_parallel_labs: If True, allows multiple labs at same time (different lab spaces).
                                 Still prevents instructor conflicts.
            allow_theory_afternoon: If True, allows theory courses in afternoon slots with relaxed
                                    instructor parallelism (for optimization when morning slots full).
        """
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        
        # Check the current generator's occupied slots first.
        if allow_parallel_labs and lecture.session_type == 'Lab':
            if self._has_overlap(day, start, end, lecture=lecture, allow_parallel_labs=True):
                return False
        else:
            if self._has_overlap(day, start, end, lecture=lecture, allow_parallel_labs=allow_parallel_labs):
                return False

        # Check against all previously scheduled lectures for global conflicts.
        if existing_lectures:
            for other in existing_lectures:
                if not getattr(other, 'day', None):
                    continue
                other_start = None
                other_end = None
                if getattr(other, 'assigned_slot', None):
                    try:
                        other_start_str, other_end_str = str(other.assigned_slot).split(' - ')
                        other_start = datetime.strptime(other_start_str.strip(), '%H:%M')
                        other_end = datetime.strptime(other_end_str.strip(), '%H:%M')
                    except Exception:
                        continue
                if other.day != day or other_start is None or other_end is None:
                    continue
                if other_start < end and other_end > start:
                    if other.instructor == lecture.instructor:
                        return False
                    if lecture.batch != 'All' and other.batch != 'All' and lecture.batch == other.batch:
                        return False
                    if lecture.section and other.section and lecture.section == other.section:
                        return False
        
        self.occupied_slots[day].append({'start': start, 'end': end, 'lecture': lecture})
        lecture.assigned_slot = f"{start_time} - {end_time}"
        lecture.assigned_period = self._get_period_label(start, end) if self.use_reference_periods else None
        lecture.day = day
        self.timetable.append({
            'Day': day,
            'Time': lecture.assigned_slot,
            'Period': lecture.assigned_period,
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
