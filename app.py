"""
Engineering College Timetable Generator
A Streamlit application for generating non-overlapping timetables with conflict detection
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import plotly.express as px
from schedule_generator import ScheduleGenerator, Lecture
from export_handler import TimetableExporter
import os

# Page configuration
st.set_page_config(
    page_title="College Timetable Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main {
        padding: 20px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
    }
    h1, h2, h3 {
        color: #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'schedule_config' not in st.session_state:
    st.session_state.schedule_config = None
if 'schedule_generators' not in st.session_state:
    st.session_state.schedule_generators = {}
if 'timetable_df' not in st.session_state:
    st.session_state.timetable_df = None
if 'lectures' not in st.session_state:
    st.session_state.lectures = []
if 'pending_courses' not in st.session_state:
    st.session_state.pending_courses = []
if 'schedule_generated' not in st.session_state:
    st.session_state.schedule_generated = False
if 'batch_sizes' not in st.session_state:
    st.session_state.batch_sizes = {}  # Store batch size for each semester
if 'saved_courses_file' not in st.session_state:
    st.session_state.saved_courses_file = os.path.join(os.getcwd(), 'saved_courses.json')

# If there is a saved courses file and no pending courses in session, load it automatically
try:
    if (not st.session_state.pending_courses) and os.path.exists(st.session_state.saved_courses_file):
        load_courses_from_disk()
except Exception:
    pass

# Helpers
def create_generator(semester: str):
    config = st.session_state.schedule_config
    if config is None:
        return None
    generator = ScheduleGenerator(
        morning_start=config['morning_start'],
        morning_end=config['morning_end'],
        short_recess_start=config['short_recess_start'],
        short_recess_end=config['short_recess_end'],
        long_recess_start=config['long_recess_start'],
        long_recess_end=config['long_recess_end'],
        use_reference_periods=config['use_reference_periods']
    )
    st.session_state.schedule_generators[semester] = generator
    return generator

def get_generator_for_semester(semester: str):
    if semester not in st.session_state.schedule_generators:
        return create_generator(semester)
    return st.session_state.schedule_generators[semester]

def instructor_has_conflict(instructor: str, day: str, start: str, end: str, assignments: list) -> bool:
    start_dt = datetime.strptime(start, "%H:%M")
    end_dt = datetime.strptime(end, "%H:%M")
    for item in assignments:
        if item['Instructor'] != instructor or item['Day'] != day:
            continue
        existing_start = item['Start']
        existing_end = item['End']
        if existing_start < end_dt and existing_end > start_dt:
            return True
    return False

def parse_batch_range(batch_str: str) -> str:
    """Convert batch range string (1-3) to readable format (Batches 1, 2, 3)"""
    if batch_str == "All" or not batch_str:
        return "All"
    if "-" in batch_str:
        parts = batch_str.split("-")
        try:
            start = int(parts[0])
            end = int(parts[1])
            batches = list(range(start, end + 1))
            return ", ".join([str(b) for b in batches])
        except ValueError:
            return batch_str
    return batch_str

def get_semester_batch_prefix(semester: str) -> str:
    semester_value = ''.join([c for c in str(semester) if c.isdigit()])
    if not semester_value:
        return 'B'
    sem = int(semester_value)
    if sem in (1, 2):
        return 'F'
    if sem in (3, 4):
        return 'S'
    if sem in (5, 6):
        return 'T'
    if sem in (7, 8):
        return 'B'
    return 'X'


def apply_rotating_batch_assignment(rows: list, batch_size_map: dict) -> list:
    """Assign rotating batches to lab courses at same time slot with daily rotation."""
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    if not rows:
        return rows
    
    # Group labs by (Semester, Time, Type='Lab')
    lab_groups = {}
    for row in rows:
        if row.get('Type') != 'Lab':
            continue
        key = (row['Semester'], row['Time'])
        if key not in lab_groups:
            lab_groups[key] = []
        lab_groups[key].append(row)
    
    # Assign rotating batches
    for (semester, time_slot), lab_rows in lab_groups.items():
        batch_size = batch_size_map.get(semester, 3)
        prefix = get_semester_batch_prefix(semester)
        
        # Group rows by day
        rows_by_day = {}
        for row in lab_rows:
            day = row['Day']
            if day not in rows_by_day:
                rows_by_day[day] = []
            rows_by_day[day].append(row)
        
        # Get unique courses in order of first appearance
        unique_courses = []
        for day in day_order:
            if day in rows_by_day:
                for row in rows_by_day[day]:
                    course_code = row['Course Code']
                    if course_code not in unique_courses:
                        unique_courses.append(course_code)
        
        # Assign batches using global course position and daily rotation
        for day_idx, day in enumerate(day_order):
            if day not in rows_by_day:
                continue
            
            rotation_offset = day_idx % batch_size
            # Sort by course code to maintain consistent ordering within each day
            day_rows_sorted = sorted(rows_by_day[day], key=lambda x: x['Course Code'])
            
            for row in day_rows_sorted:
                # Get global course index from unique_courses list
                course_idx = unique_courses.index(row['Course Code'])
                # Apply rotation: add day offset to course index
                batch_num = ((course_idx + rotation_offset) % batch_size) + 1
                row['Batch'] = f"{prefix}{batch_num}"
    
    return rows


def save_courses_to_disk(path: str = None):
    path = path or st.session_state.saved_courses_file
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.pending_courses, f, ensure_ascii=False, indent=2)
        return True, path
    except Exception as e:
        return False, str(e)


def load_courses_from_disk(path: str = None):
    path = path or st.session_state.saved_courses_file
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Validate and normalize loaded data
        normalized = []
        for item in data:
            # minimal validation
            if not item.get('code') or not item.get('name') or not item.get('instructor'):
                continue
            item.setdefault('type', 'Theory')
            item.setdefault('semester', '1st')
            item.setdefault('section', 'A')
            item.setdefault('branch', '')
            item.setdefault('duration', 1.0 if item.get('type') == 'Theory' else 1.5)
            item.setdefault('batch', 'All')
            normalized.append(item)
        st.session_state.pending_courses = normalized
        return True, path
    except Exception as e:
        return False, str(e)


def safe_rerun():
    """Call Streamlit rerun safely across different Streamlit versions."""
    try:
        rerun = getattr(st, 'rerun', None)
        if callable(rerun):
            rerun()
            return

        exp_rerun = getattr(st, 'experimental_rerun', None)
        if callable(exp_rerun):
            exp_rerun()
            return

        stop = getattr(st, 'stop', None)
        if callable(stop):
            # Best-effort fallback: stop current script
            stop()
    except Exception:
        # If rerun isn't available in this environment, silently continue
        return


def _get_day_order(day: str) -> int:
    order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
    return order.get(day, 99)


def assign_period_numbers(rows: list) -> list:
    """Assign numeric period labels for rows with flexible timing."""
    rows_by_sem_day = {}
    for row in rows:
        key = (row.get('Semester', ''), row.get('Day', ''))
        rows_by_sem_day.setdefault(key, []).append(row)

    for key, group in rows_by_sem_day.items():
        def parse_start_time(r):
            time_value = r.get('Time', '')
            if isinstance(time_value, str) and '-' in time_value:
                start = time_value.split('-')[0].strip()
                try:
                    return datetime.strptime(start, '%H:%M')
                except Exception:
                    return datetime.min
            return datetime.min

        group.sort(key=parse_start_time)
        for idx, row in enumerate(group, start=1):
            if row.get('Period') and isinstance(row['Period'], str) and row['Period'].startswith('Period'):
                continue
            row['Period'] = f"P{idx}"

    return rows


def reset_schedule_state():
    st.session_state.schedule_generators = {}
    st.session_state.timetable_df = None
    st.session_state.lectures = []
    st.session_state.schedule_generated = False
    st.session_state.generated_semesters = []

# Header
st.title("📚 Engineering College Timetable Generator")
st.markdown("---")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("College Hours")
        morning_start = st.time_input("Morning Start Time", value=datetime.strptime("08:30", "%H:%M").time())
        morning_end = st.time_input("Morning End Time", value=datetime.strptime("17:00", "%H:%M").time())
    
    with col2:
        st.subheader("Recess Timings")
        short_recess_start = st.time_input("Short Recess Start", value=datetime.strptime("10:30", "%H:%M").time())
        short_recess_end = st.time_input("Short Recess End", value=datetime.strptime("10:45", "%H:%M").time())
        
        long_recess_start = st.time_input("Long Recess Start", value=datetime.strptime("13:00", "%H:%M").time())
        long_recess_end = st.time_input("Long Recess End", value=datetime.strptime("14:00", "%H:%M").time())

    st.subheader("Schedule Layout")
    schedule_layout = st.radio(
        "Choose timetable style",
        ["Reference period layout (image style)", "Flexible custom timing"],
        index=0
    )
    
    if st.button("Initialize Schedule", use_container_width=True, key="init_btn"):
        try:
            st.session_state.schedule_config = {
                'morning_start': morning_start.strftime("%H:%M"),
                'morning_end': morning_end.strftime("%H:%M"),
                'short_recess_start': short_recess_start.strftime("%H:%M"),
                'short_recess_end': short_recess_end.strftime("%H:%M"),
                'long_recess_start': long_recess_start.strftime("%H:%M"),
                'long_recess_end': long_recess_end.strftime("%H:%M"),
                'use_reference_periods': schedule_layout == "Reference period layout (image style)"
            }
            reset_schedule_state()
            st.success("✅ Schedule initialized successfully!")
        except Exception as e:
            st.error(f"Error initializing schedule: {str(e)}")

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Add Classes",
    "🗓️ View Timetable",
    "👨‍🏫 Instructor Schedule",
    "📊 Analytics",
    "💾 Export"
])

# ===== TAB 1: Add Classes =====
with tab1:
    st.header("Add Classes to Timetable")
    
    if st.session_state.schedule_config is None:
        st.warning("⚠️ Please initialize the schedule in the sidebar first!")
    else:
        st.subheader("📝 Enter Course Details")
        st.info("Add courses below and click 'Generate Schedule' to automatically assign times!")

        # Upload / Save / Load facilities
        st.markdown("**Upload course list (CSV / Excel)**")
        uploaded_file = st.file_uploader("Upload CSV or Excel file with columns: Course Code, Course Name, Instructor, Type, Semester, Section, Branch, Duration (optional), Batch (optional)", type=['csv', 'xlsx'], key='upload_courses')
        if uploaded_file is not None:
            try:
                if uploaded_file.name.lower().endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                # Normalize column names
                df_columns = {c.lower().strip(): c for c in df.columns}
                def col_lookup(name):
                    return df_columns.get(name.lower())

                added = 0
                for _, row in df.iterrows():
                    code = row.get(col_lookup('course code')) or row.get(col_lookup('code'))
                    name = row.get(col_lookup('course name')) or row.get(col_lookup('name'))
                    instructor = row.get(col_lookup('instructor'))
                    session_type = row.get(col_lookup('type')) or 'Theory'
                    semester = row.get(col_lookup('semester')) or '1st'
                    section = row.get(col_lookup('section')) or 'A'
                    branch = row.get(col_lookup('branch')) or ''
                    duration = row.get(col_lookup('duration')) if not pd.isna(row.get(col_lookup('duration'))) else (1.0 if str(session_type).lower().startswith('t') else 1.5)
                    batch = row.get(col_lookup('batch')) or 'All'

                    if not code or not name or not instructor:
                        continue

                    course_data = {
                        'code': str(code).strip(),
                        'name': str(name).strip(),
                        'instructor': str(instructor).strip(),
                        'type': str(session_type).strip(),
                        'semester': str(semester).strip(),
                        'section': str(section).strip(),
                        'branch': str(branch).strip(),
                        'duration': float(duration),
                        'batch': str(batch).strip()
                    }
                    existing = [p for p in st.session_state.pending_courses if p['code'] == course_data['code']]
                    if not existing:
                        st.session_state.pending_courses.append(course_data)
                        added += 1

                if added:
                    st.success(f"✅ Loaded {added} courses from upload.")
                    # auto-save after upload
                    save_courses_to_disk()
                    safe_rerun()
                else:
                    st.info("No valid course rows found in uploaded file or duplicates skipped.")
            except Exception as e:
                st.error(f"Failed to parse uploaded file: {e}")

        # Save / Load buttons
        col_save, col_load = st.columns(2)
        with col_save:
            if st.button("💾 Save Courses", key='save_courses_btn'):
                ok, msg = save_courses_to_disk()
                if ok:
                    st.success(f"Saved courses to {msg}")
                else:
                    st.error(f"Failed to save courses: {msg}")
        with col_load:
            if st.button("📂 Load Saved Courses", key='load_courses_btn'):
                ok, msg = load_courses_from_disk()
                if ok:
                    st.success(f"Loaded courses from {msg}")
                    safe_rerun()
                else:
                    st.error(f"Failed to load courses: {msg}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            course_code = st.text_input("Course Code", placeholder="CS101", key="code_input")
            session_type = st.selectbox("Session Type", ["Theory", "Lab"], key="type_select")
        
        with col2:
            course_name = st.text_input("Course Name", placeholder="Data Structures", key="name_input")
            semester = st.selectbox("Semester", ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"], key="sem_select")
        
        with col3:
            instructor = st.text_input("Instructor Name", placeholder="Dr. John Doe", key="instr_input")
            section = st.selectbox("Section", ["A", "B", "C", "D"], key="sec_select")

        branch = st.selectbox(
            "DEPARTMENT ",
            [
                "Artificial Intelligence & Data Science Engineering",
                "BS&H",
                "CIVIL Engineering",
                "Computer Science & Engineering",
                "Electrical Engineering",
                "Electronics & Telecommunication Engineering",
                "Mechanical Engineering",
                "Bachelor of Computer Application",
                "Master Computer Application"
            ],
            key="branch_select"
        )
        
        # Batch size configuration for the selected semester
        st.subheader("🏷️ Lab Batch Configuration")
        batch_config_col1, batch_config_col2, batch_config_col3 = st.columns(3)
        with batch_config_col1:
            st.write(f"**Semester**: {semester}")
        with batch_config_col2:
            batch_size = st.number_input(
                "Lab Batch Size",
                min_value=1,
                max_value=6,
                value=st.session_state.batch_sizes.get(semester, 3),
                key=f"batch_size_input_{semester}"
            )
            st.session_state.batch_sizes[semester] = batch_size
        with batch_config_col3:
            batch_labels = ", ".join([str(i) for i in range(1, batch_size + 1)])
            st.info(f"Batches: {batch_labels}")
        
        # Lab batch assignment (auto-generated based on batch size)
        batch = "All"
        if session_type == "Lab":
            st.success(f"✅ Lab batches for {semester}: {batch_labels} (auto-assigned)")
        
        # Set duration based on session type
        if session_type == "Theory":
            duration = 1.0
            st.info("📝 Theory lectures: 1 hour")
        else:
            duration = 1.5
            st.info("🔬 Lab sessions: 1.5 hours")
        
        # Add course button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Add Course", use_container_width=True):
                if not all([course_code, course_name, instructor]):
                    st.error("Please fill in Course Code, Name, and Instructor!")
                else:
                    # Check if course already exists
                    existing = [p for p in st.session_state.pending_courses if p['code'] == course_code]
                    if existing:
                        st.error(f"Course {course_code} already added!")
                    else:
                        # Auto-assign batch for lab courses
                        if session_type == 'Lab':
                            batch = f"1-{batch_size}"  # Store as range, e.g., "1-3"
                        else:
                            batch = "All"
                        
                        course_data = {
                            'code': course_code,
                            'name': course_name,
                            'instructor': instructor,
                            'type': session_type,
                            'semester': semester,
                            'section': section,
                            'branch': branch,
                            'duration': duration,
                            'batch': batch if batch else 'All'
                        }
                        st.session_state.pending_courses.append(course_data)
                        # Auto-save after adding course
                        ok, msg = save_courses_to_disk()
                        if ok:
                            st.success(f"✅ {course_code} added and saved to disk.")
                        else:
                            st.warning(f"{course_code} added but failed to save: {msg}")
                        st.rerun()
        
        # Display pending courses
        if st.session_state.pending_courses:
            st.subheader("📋 Courses to Schedule")
            pending_df = pd.DataFrame(st.session_state.pending_courses)
            # Create a display DataFrame with formatted batch info
            pending_df_display = pending_df[['code', 'name', 'instructor', 'type', 'semester', 'section', 'branch', 'batch']].copy()
            pending_df_display['batch'] = pending_df_display['batch'].apply(parse_batch_range)
            pending_df_display = pending_df_display.rename(columns={'batch': 'batches'})
            st.dataframe(pending_df_display, use_container_width=True)
            st.caption("💡 For labs: Batches are auto-assigned based on batch size configuration per semester")
            
            # Remove course option
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.pending_courses:
                    course_to_remove = st.selectbox(
                        "Select course to remove",
                        [c['code'] for c in st.session_state.pending_courses],
                        key="remove_select"
                    )
                    if st.button("🗑️ Remove Course", use_container_width=True):
                        st.session_state.pending_courses = [
                            c for c in st.session_state.pending_courses if c['code'] != course_to_remove
                        ]
                        st.success(f"✅ {course_to_remove} removed!")
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.session_state.pending_courses = []
                    st.success("✅ All courses cleared!")
                    st.rerun()
            
            st.markdown("---")
            
            # Generate Schedule button
            if st.button("🚀 GENERATE SCHEDULE", use_container_width=True, key="generate_btn"):
                with st.spinner("⏳ Generating timetable..."):
                    try:
                        reset_schedule_state()
                        
                        failed_courses = []
                        global_assignments = []
                        batch_size_map = st.session_state.batch_sizes  # Get batch sizes for each semester
                        
                        # Group courses by type and semester
                        lab_courses_by_semester = {}
                        theory_courses = []
                        
                        for course_data in st.session_state.pending_courses:
                            if course_data['type'] == 'Lab':
                                sem = course_data['semester']
                                if sem not in lab_courses_by_semester:
                                    lab_courses_by_semester[sem] = []
                                lab_courses_by_semester[sem].append(course_data)
                            else:
                                theory_courses.append(course_data)
                        
                        # Step 1: Schedule lab courses by choosing valid lab slots per semester
                        for sem_idx, (semester, lab_courses) in enumerate(lab_courses_by_semester.items()):
                            generator = get_generator_for_semester(semester)
                            if generator is None:
                                for course in lab_courses:
                                    failed_courses.append(course['code'])
                                continue
                            
                            duration = lab_courses[0]['duration']
                            candidate_slots = []
                            # Find lab slots that are available on all days
                            monday_slots = generator.get_available_slots('Monday', duration, session_type='Lab')
                            for slot_start, slot_end in monday_slots:
                                if all(
                                    (slot_start, slot_end) in generator.get_available_slots(day, duration, session_type='Lab')
                                    for day in ['Tuesday', 'Wednesday', 'Thursday', 'Friday']
                                ):
                                    candidate_slots.append((slot_start, slot_end))
                            # If no candidate slots found, all lab courses for this semester will likely fail
                            if not candidate_slots:
                                for course in lab_courses:
                                    failed_courses.append(course['code'])
                                continue

                            # Rotate candidate slot order based on semester number/index to avoid same timing across semesters
                            sem_digits = ''.join([c for c in str(semester) if c.isdigit()])
                            try:
                                sem_num = int(sem_digits) if sem_digits else sem_idx + 1
                            except Exception:
                                sem_num = sem_idx + 1

                            offset = (sem_num - 1) % len(candidate_slots)
                            ordered_slots = candidate_slots[offset:] + candidate_slots[:offset]

                            used_slots = set()
                            all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

                            for lab_course in lab_courses:
                                assigned = False
                                # Try to pick an unused slot first
                                for slot_start, slot_end in ordered_slots:
                                    if (slot_start, slot_end) in used_slots:
                                        continue

                                    slot_valid = all(
                                        (slot_start, slot_end) in generator.get_available_slots(day, duration, session_type='Lab')
                                        and not instructor_has_conflict(
                                            lab_course['instructor'],
                                            day,
                                            slot_start,
                                            slot_end,
                                            global_assignments
                                        )
                                        for day in all_days
                                    )
                                    if not slot_valid:
                                        continue

                                    # Assign this slot for the course across all days
                                    successful_assign = True
                                    for day in all_days:
                                        lecture = Lecture(
                                            course_code=lab_course['code'],
                                            course_name=lab_course['name'],
                                            instructor=lab_course['instructor'],
                                            session_type=lab_course['type'],
                                            sem=lab_course['semester'],
                                            section=lab_course['section'],
                                            branch=lab_course.get('branch', ''),
                                            duration=lab_course['duration'],
                                            batch='All'
                                        )
                                        # Do not allow unlimited parallel labs within a semester by default
                                        if not generator.assign_lecture(lecture, day, slot_start, slot_end, allow_parallel_labs=False):
                                            successful_assign = False
                                            break
                                        global_assignments.append({
                                            'Instructor': lecture.instructor,
                                            'Day': day,
                                            'Start': datetime.strptime(slot_start, "%H:%M"),
                                            'End': datetime.strptime(slot_end, "%H:%M")
                                        })
                                        st.session_state.lectures.append(lecture)

                                    if successful_assign:
                                        assigned = True
                                        used_slots.add((slot_start, slot_end))
                                        break

                                # If not assigned, allow reuse (parallel labs) as fallback but still check instructor conflict
                                if not assigned:
                                    for slot_start, slot_end in ordered_slots:
                                        slot_valid = all(
                                            (slot_start, slot_end) in generator.get_available_slots(day, duration, session_type='Lab')
                                            and not instructor_has_conflict(
                                                lab_course['instructor'],
                                                day,
                                                slot_start,
                                                slot_end,
                                                global_assignments
                                            )
                                            for day in all_days
                                        )
                                        if not slot_valid:
                                            continue

                                        for day in all_days:
                                            lecture = Lecture(
                                                course_code=lab_course['code'],
                                                course_name=lab_course['name'],
                                                instructor=lab_course['instructor'],
                                                session_type=lab_course['type'],
                                                sem=lab_course['semester'],
                                                section=lab_course['section'],
                                                branch=lab_course.get('branch', ''),
                                                duration=lab_course['duration'],
                                                batch='All'
                                            )
                                            generator.assign_lecture(lecture, day, slot_start, slot_end, allow_parallel_labs=True)
                                            global_assignments.append({
                                                'Instructor': lecture.instructor,
                                                'Day': day,
                                                'Start': datetime.strptime(slot_start, "%H:%M"),
                                                'End': datetime.strptime(slot_end, "%H:%M")
                                            })
                                            st.session_state.lectures.append(lecture)
                                        assigned = True
                                        break

                                if not assigned:
                                    failed_courses.append(lab_course['code'])
                        
                        # Step 2: Schedule theory courses
                        for course_data in theory_courses:
                            generator = get_generator_for_semester(course_data['semester'])
                            if generator is None:
                                failed_courses.append(course_data['code'])
                                continue

                            assigned_days = []
                            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                                available_slots = generator.get_available_slots(day, course_data['duration'])
                                for slot_start, slot_end in available_slots:
                                    if instructor_has_conflict(
                                        course_data['instructor'],
                                        day,
                                        slot_start,
                                        slot_end,
                                        global_assignments
                                    ):
                                        continue

                                    lecture = Lecture(
                                        course_code=course_data['code'],
                                        course_name=course_data['name'],
                                        instructor=course_data['instructor'],
                                        session_type=course_data['type'],
                                        sem=course_data['semester'],
                                        section=course_data['section'],
                                        branch=course_data.get('branch', ''),
                                        duration=course_data['duration'],
                                        batch='All'
                                    )
                                    if generator.assign_lecture(lecture, day, slot_start, slot_end):
                                        global_assignments.append({
                                            'Instructor': lecture.instructor,
                                            'Day': day,
                                            'Start': datetime.strptime(slot_start, "%H:%M"),
                                            'End': datetime.strptime(slot_end, "%H:%M")
                                        })
                                        st.session_state.lectures.append(lecture)
                                        assigned_days.append(day)
                                        break

                            if not assigned_days:
                                failed_courses.append(course_data['code'])
                        
                        # Build combined timetable across semester generators
                        all_rows = []
                        for gen in st.session_state.schedule_generators.values():
                            gen_df = gen.get_complete_timetable()
                            if isinstance(gen_df, pd.DataFrame) and not gen_df.empty:
                                all_rows.extend(gen_df.to_dict(orient='records'))
                        
                        # Apply rotating batch assignment for labs
                        if all_rows:
                            all_rows = apply_rotating_batch_assignment(all_rows, batch_size_map)
                            all_rows = assign_period_numbers(all_rows)
                            all_rows = sorted(
                                all_rows,
                                key=lambda r: (
                                    int(''.join([c for c in str(r.get('Semester', '')) if c.isdigit()]) or 0),
                                    _get_day_order(r.get('Day', '')),
                                    datetime.strptime(str(r.get('Time', '')).split('-')[0].strip(), '%H:%M') if isinstance(r.get('Time', ''), str) and '-' in r.get('Time', '') else datetime.min
                                )
                            )
                        
                        st.session_state.timetable_df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
                        st.session_state.schedule_generated = True
                        st.session_state.pending_courses = []
                        
                        if failed_courses:
                            st.warning(f"⚠️ Could not schedule: {', '.join(failed_courses)}. Try adjusting timings or removing some courses.")
                        else:
                            st.success(f"✅ Schedule generated successfully for {len(st.session_state.lectures)} courses!")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error generating schedule: {str(e)}")
        else:
            if st.session_state.schedule_generated:
                st.subheader("✅ Schedule Generated!")
                st.dataframe(st.session_state.timetable_df, use_container_width=True)
                
                if st.button("🔄 Start New Schedule", use_container_width=True):
                    reset_schedule_state()
                    st.session_state.schedule_config = None
                    st.session_state.pending_courses = []
                    st.rerun()

# ===== TAB 2: View Timetable =====
with tab2:
    st.header("📅 Complete Timetable")
    
    if st.session_state.timetable_df is None or st.session_state.timetable_df.empty:
        st.info("ℹ️ No timetable generated yet. Add courses and click 'Generate Schedule' in the 'Add Classes' tab.")
    else:
        semester_options = sorted(st.session_state.timetable_df['Semester'].unique())
        selected_semester_view = st.selectbox("Select Semester to View", ["All"] + semester_options, index=0)
        
        selected_view_day = st.selectbox("Select Day to View", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        display_df = st.session_state.timetable_df
        if selected_semester_view != "All":
            display_df = display_df[display_df['Semester'] == selected_semester_view]
        
        # Display complete timetable
        st.subheader("Complete Timetable")
        st.dataframe(display_df, use_container_width=True)
        
        # Display day-wise timetable
        st.subheader("📆 Day-wise View")
        day_timetable = display_df[display_df['Day'] == selected_view_day]
        if day_timetable.empty:
            st.info(f"No classes scheduled for {selected_view_day} in {selected_semester_view} semester")
        else:
            st.dataframe(day_timetable, use_container_width=True)
        
        # Statistics
        st.subheader("📊 Quick Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Classes", len(display_df))
        
        with col2:
            theory_count = len(display_df[display_df['Type'] == 'Theory'])
            st.metric("Theory Lectures", theory_count)
        
        with col3:
            lab_count = len(display_df[display_df['Type'] == 'Lab'])
            st.metric("Lab Sessions", lab_count)
        
        with col4:
            instructors = display_df['Instructor'].nunique()
            st.metric("Instructors", instructors)

# ===== TAB 3: Instructor Schedule =====
with tab3:
    st.header("👨‍🏫 Instructor Schedule")
    
    if st.session_state.timetable_df is None or st.session_state.timetable_df.empty:
        st.info("ℹ️ No timetable generated yet.")
    else:
        semester_options = sorted(st.session_state.timetable_df['Semester'].unique())
        selected_semester_instructor = st.selectbox("Select Semester", ["All"] + semester_options)
        
        display_df = st.session_state.timetable_df
        if selected_semester_instructor != "All":
            display_df = display_df[display_df['Semester'] == selected_semester_instructor]
        
        instructors = display_df['Instructor'].unique()
        selected_instructor = st.selectbox("Select Instructor", instructors)
        
        instructor_schedule = display_df[display_df['Instructor'] == selected_instructor]
        
        if instructor_schedule.empty:
            st.info(f"No classes found for {selected_instructor}")
        else:
            st.dataframe(instructor_schedule, use_container_width=True)
            
            # Summary
            st.subheader("Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Classes", len(instructor_schedule))
            with col2:
                days_teaching = instructor_schedule['Day'].nunique()
                st.metric("Days Teaching", days_teaching)

# ===== TAB 4: Analytics =====
with tab4:
    st.header("📊 Timetable Analytics")
    
    if st.session_state.timetable_df is None or st.session_state.timetable_df.empty:
        st.info("ℹ️ No timetable generated yet.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Classes by Day")
            day_counts = st.session_state.timetable_df['Day'].value_counts()
            st.bar_chart(day_counts)
        
        with col2:
            st.subheader("Classes by Type")
            type_counts = st.session_state.timetable_df['Type'].value_counts()
            pie_fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Theory vs Lab Distribution"
            )
            st.plotly_chart(pie_fig, use_container_width=True)
        
        st.subheader("Classes by Semester")
        sem_counts = st.session_state.timetable_df['Semester'].value_counts().sort_index()
        st.bar_chart(sem_counts)
        
        st.subheader("Load Distribution")
        instructor_load = st.session_state.timetable_df['Instructor'].value_counts()
        st.bar_chart(instructor_load)

# ===== TAB 5: Export =====
with tab5:
    st.header("💾 Export Timetable")
    
    if st.session_state.timetable_df is None or st.session_state.timetable_df.empty:
        st.info("ℹ️ No timetable generated yet. Add courses and click 'Generate Schedule' to export.")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Export as CSV")
            csv_data = TimetableExporter.export_to_csv(st.session_state.timetable_df)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="timetable.csv",
                mime="text/csv",
                use_container_width=True
            )
            matrix_csv_data = TimetableExporter.export_timetable_matrix_csv(st.session_state.timetable_df)
            st.download_button(
                label="📥 Download Matrix CSV",
                data=matrix_csv_data,
                file_name="timetable_matrix.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.subheader("Export as Word")
            word_data = TimetableExporter.export_to_word(
                st.session_state.timetable_df,
                title="College Timetable - Complete Schedule"
            )
            st.download_button(
                label="📥 Download Word",
                data=word_data,
                file_name="timetable.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            matrix_word_data = TimetableExporter.export_timetable_matrix_word(
                st.session_state.timetable_df,
                title="College Timetable - Timetable Matrix"
            )
            st.download_button(
                label="📥 Download Matrix Word",
                data=matrix_word_data,
                file_name="timetable_matrix.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        with col3:
            st.subheader("Export Day-wise Word")
            word_daywise = TimetableExporter.export_day_wise(st.session_state.timetable_df)
            st.download_button(
                label="📥 Download Day-wise",
                data=word_daywise,
                file_name="timetable_daywise.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        st.markdown("---")
        st.subheader("📋 Export Options")
        
        semester_options = sorted(st.session_state.timetable_df['Semester'].unique())
        selected_export_semester = st.selectbox("Select Semester to Export", ["All"] + semester_options, key="export_semester_select")
        export_df = st.session_state.timetable_df
        if selected_export_semester != "All":
            export_df = export_df[export_df['Semester'] == selected_export_semester]
        
        # Export specific day
        col1, col2 = st.columns(2)
        with col1:
            export_day = st.selectbox("Select Day to Export", 
                                     ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                     key="export_day_select")
            day_timetable = export_df[export_df['Day'] == export_day]
            if not day_timetable.empty:
                csv_day = TimetableExporter.export_to_csv(day_timetable)
                st.download_button(
                    label=f"📥 Download {export_day} (CSV)",
                    data=csv_day,
                    file_name=f"timetable_{selected_export_semester.lower()}_{export_day.lower()}.csv" if selected_export_semester != 'All' else f"timetable_{export_day.lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # Export instructor schedule
        with col2:
            if not export_df.empty:
                instructors = export_df['Instructor'].unique()
                selected_inst = st.selectbox("Select Instructor to Export", instructors, key="export_inst_select")
                inst_schedule = export_df[export_df['Instructor'] == selected_inst]
                if not inst_schedule.empty:
                    csv_inst = TimetableExporter.export_to_csv(inst_schedule)
                    st.download_button(
                        label=f"📥 Download {selected_inst} Schedule",
                        data=csv_inst,
                        file_name=f"timetable_{selected_export_semester.lower()}_{selected_inst.replace(' ', '_')}.csv" if selected_export_semester != 'All' else f"timetable_{selected_inst.replace(' ', '_')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Engineering College Timetable Generator | Version 1.0<br>"
    "Built with Streamlit, Python & ❤️"
    "</div>",
    unsafe_allow_html=True
)
