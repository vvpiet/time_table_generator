import importlib.util
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent

spec_schedule = importlib.util.spec_from_file_location('schedule_generator', ROOT / 'schedule_generator.py')
schedule_module = importlib.util.module_from_spec(spec_schedule)
spec_schedule.loader.exec_module(schedule_module)
normalize_session_type = schedule_module.normalize_session_type

spec_export = importlib.util.spec_from_file_location('export_handler', ROOT / 'export_handler.py')
export_module = importlib.util.module_from_spec(spec_export)
spec_export.loader.exec_module(export_module)
TimetableExporter = export_module.TimetableExporter


def test_normalize_session_type_rotation_is_treated_as_theory():
    assert normalize_session_type('Rotation') == 'Theory'
    assert normalize_session_type('rotational') == 'Theory'


def test_export_matrix_includes_course_name_and_filters_out_of_config_slots():
    df = pd.DataFrame([
        {
            'Day': 'Monday',
            'Time': '09:00 - 10:00',
            'Course Code': 'TH101',
            'Course Name': 'Engineering Mathematics',
            'Branch': 'CSE',
            'Type': 'Theory',
            'Instructor': 'Prof A',
            'Semester': '4th',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 4,
        },
        {
            'Day': 'Monday',
            'Time': '16:00 - 17:00',
            'Course Code': 'TH102',
            'Course Name': 'Outside Config Session',
            'Branch': 'CSE',
            'Type': 'Theory',
            'Instructor': 'Prof B',
            'Semester': '4th',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 4,
        },
    ])

    config = {
        'morning_start': '08:30',
        'morning_end': '13:00',
        'short_recess_start': '10:30',
        'short_recess_end': '10:45',
        'long_recess_start': '13:00',
        'long_recess_end': '14:00',
    }

    word_bytes = TimetableExporter.export_timetable_matrix_word(df, config=config)
    assert len(word_bytes) > 0

    # The exporter should not include out-of-config slots in the matrix.
    filtered = TimetableExporter._filter_timetable_for_config(df, config)
    assert len(filtered) == 1
    assert filtered.iloc[0]['Course Name'] == 'Engineering Mathematics'


def test_export_to_csv_filters_out_of_config_slots():
    df = pd.DataFrame([
        {
            'Day': 'Monday',
            'Time': '09:00 - 10:00',
            'Course Code': 'TH101',
            'Course Name': 'Engineering Mathematics',
            'Branch': 'CSE',
            'Type': 'Theory',
            'Instructor': 'Prof A',
            'Semester': '4th',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 4,
        },
        {
            'Day': 'Monday',
            'Time': '16:00 - 17:00',
            'Course Code': 'TH102',
            'Course Name': 'Outside Config Session',
            'Branch': 'CSE',
            'Type': 'Theory',
            'Instructor': 'Prof B',
            'Semester': '4th',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 4,
        },
    ])

    config = {
        'morning_start': '08:30',
        'morning_end': '13:00',
        'short_recess_start': '10:30',
        'short_recess_end': '10:45',
        'long_recess_start': '13:00',
        'long_recess_end': '14:00',
    }

    csv_bytes = TimetableExporter.export_to_csv(df, config=config)
    csv_text = csv_bytes.decode('utf-8')
    assert 'Engineering Mathematics' in csv_text
    assert 'Outside Config Session' not in csv_text
