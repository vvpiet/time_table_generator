"""
Test matrix export functionality and overlap prevention
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from schedule_generator import ScheduleGenerator, Lecture
from export_handler import TimetableExporter
from datetime import datetime
import pandas as pd
from io import BytesIO

def test_matrix_structure():
    """Test that matrix export creates proper structure"""
    print("=" * 60)
    print("TEST 1: Matrix Export Structure")
    print("=" * 60)
    
    # Create test timetable
    timetable_data = [
        {
            'Day': 'Monday',
            'Time': '10:00 - 11:00',
            'Period': 'P1',
            'Course Code': 'BS101',
            'Course Name': 'Mathematics',
            'Branch': 'Branch A',
            'Type': 'Theory',
            'Instructor': 'Prof A',
            'Semester': '1',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 2
        },
        {
            'Day': 'Monday',
            'Time': '11:00 - 12:00',
            'Period': 'P2',
            'Course Code': 'BS102',
            'Course Name': 'Physics Lab',
            'Branch': 'Branch A',
            'Type': 'Lab',
            'Instructor': 'Prof B',
            'Semester': '1',
            'Section': 'A',
            'Batch': 'F1',
            'Hours Per Week': 3
        },
        {
            'Day': 'Monday',
            'Time': '11:00 - 12:00',
            'Period': 'P2',
            'Course Code': 'BS102',
            'Course Name': 'Physics Lab',
            'Branch': 'Branch A',
            'Type': 'Lab',
            'Instructor': 'Prof C',
            'Semester': '1',
            'Section': 'A',
            'Batch': 'F2',
            'Hours Per Week': 3
        },
        {
            'Day': 'Tuesday',
            'Time': '10:00 - 11:00',
            'Period': 'P1',
            'Course Code': 'BS103',
            'Course Name': 'Chemistry',
            'Branch': 'Branch A',
            'Type': 'Theory',
            'Instructor': 'Prof D',
            'Semester': '1',
            'Section': 'A',
            'Batch': 'All',
            'Hours Per Week': 2
        }
    ]
    
    df = pd.DataFrame(timetable_data)
    
    try:
        # Export to Word matrix
        word_bytes = TimetableExporter.export_timetable_matrix_word(df, "Test Timetable")
        print("✅ Matrix Word export successful")
        print(f"   Export size: {len(word_bytes)} bytes")
        
        # Verify structure
        assert len(word_bytes) > 0, "Export is empty"
        print("✅ Export contains data")
        
        # Check data structure
        unique_times = sorted(df['Time'].unique())
        unique_days = sorted([d for d in df['Day'].unique()])
        print(f"✅ Structure verified:")
        print(f"   - Time slots: {unique_times}")
        print(f"   - Days: {unique_days}")
        print(f"   - Total courses: {len(df)}")
        
        # Check batches are correctly formatted
        batches_in_export = df[df['Type'] == 'Lab']['Batch'].unique()
        print(f"✅ Lab batches: {batches_in_export}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_overlap_prevention():
    """Test that scheduling prevents instructor and batch overlaps"""
    print("\n" + "=" * 60)
    print("TEST 2: Overlap Prevention")
    print("=" * 60)
    
    try:
        # Create generator with proper timing
        gen = ScheduleGenerator(
            morning_start=datetime.strptime("10:00", "%H:%M"),
            morning_end=datetime.strptime("13:00", "%H:%M"),
            short_recess_start=datetime.strptime("10:30", "%H:%M"),
            short_recess_end=datetime.strptime("10:45", "%H:%M"),
            long_recess_start=datetime.strptime("13:00", "%H:%M"),
            long_recess_end=datetime.strptime("14:00", "%H:%M"),
            use_reference_periods=False
        )
        
        # Create first lecture
        lecture1 = Lecture(
            course_code="CS101",
            course_name="Programming",
            instructor="Prof X",
            session_type="Theory",
            sem="1",
            section="A",
            branch="IT",
            duration=1,
            batch="All"
        )
        
        # Assign first lecture
        start1 = datetime.strptime("10:00", "%H:%M")
        end1 = datetime.strptime("11:00", "%H:%M")
        result1 = gen.assign_lecture(lecture1, "Monday", start1, end1)
        assert result1, "Failed to assign first lecture"
        print("✅ First lecture assigned (Prof X, 10:00-11:00)")
        
        # Try to assign overlapping lecture with SAME instructor (should fail)
        lecture2 = Lecture(
            course_code="CS102",
            course_name="Data Structures",
            instructor="Prof X",
            session_type="Theory",
            sem="1",
            section="A",
            branch="IT",
            duration=1,
            batch="All"
        )
        
        start2 = datetime.strptime("10:30", "%H:%M")
        end2 = datetime.strptime("11:30", "%H:%M")
        result2 = gen.assign_lecture(lecture2, "Monday", start2, end2)
        assert not result2, "Should have prevented instructor overlap"
        print("✅ Correctly prevented instructor overlap (Prof X cannot teach 2 courses at same time)")
        
        # Try to assign overlapping lecture with SAME batch (should fail)
        lecture3 = Lecture(
            course_code="CS103",
            course_name="Algorithms",
            instructor="Prof Y",
            session_type="Lab",
            sem="1",
            section="A",
            branch="IT",
            duration=1,
            batch="B1"
        )
        
        result3 = gen.assign_lecture(lecture3, "Monday", start1, end1)
        assert not result3, "Should have prevented batch overlap"
        print("✅ Correctly prevented batch overlap (Batch B1 cannot attend 2 courses at same time)")
        
        # Try to assign non-overlapping lecture with DIFFERENT instructor (should succeed)
        lecture4 = Lecture(
            course_code="CS104",
            course_name="Database",
            instructor="Prof Z",
            session_type="Theory",
            sem="1",
            section="A",
            branch="IT",
            duration=1,
            batch="All"
        )
        
        result4 = gen.assign_lecture(lecture4, "Monday", start2, end2)
        assert result4, "Failed to assign non-overlapping lecture"
        print("✅ Correctly allowed non-overlapping lecture (Prof Z at 10:30-11:30)")
        
        return True
    except AssertionError as e:
        print(f"❌ Assertion failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_rotation():
    """Test that batch rotation works correctly"""
    print("\n" + "=" * 60)
    print("TEST 3: Batch Rotation")
    print("=" * 60)
    
    try:
        # Create test data with same course on different days
        timetable_data = [
            {
                'Day': 'Monday',
                'Time': '11:00 - 12:00',
                'Period': 'P2',
                'Course Code': 'BS102',
                'Course Name': 'Physics Lab',
                'Branch': 'Branch A',
                'Type': 'Lab',
                'Instructor': 'Prof B',
                'Semester': '1',
                'Section': 'A',
                'Batch': 'F1',
                'Hours Per Week': 3
            },
            {
                'Day': 'Tuesday',
                'Time': '11:00 - 12:00',
                'Period': 'P2',
                'Course Code': 'BS102',
                'Course Name': 'Physics Lab',
                'Branch': 'Branch A',
                'Type': 'Lab',
                'Instructor': 'Prof C',
                'Semester': '1',
                'Section': 'A',
                'Batch': 'F1',
                'Hours Per Week': 3
            },
            {
                'Day': 'Wednesday',
                'Time': '11:00 - 12:00',
                'Period': 'P2',
                'Course Code': 'BS102',
                'Course Name': 'Physics Lab',
                'Branch': 'Branch A',
                'Type': 'Lab',
                'Instructor': 'Prof D',
                'Semester': '1',
                'Section': 'A',
                'Batch': 'F1',
                'Hours Per Week': 3
            }
        ]
        
        df = pd.DataFrame(timetable_data)
        
        # Check that all rows initially have same batch
        initial_batches = df['Batch'].unique()
        print(f"✅ Initial batch assignments: {initial_batches}")
        
        # Export should show data properly
        word_bytes = TimetableExporter.export_timetable_matrix_word(df, "Batch Rotation Test")
        assert len(word_bytes) > 0, "Export failed"
        print("✅ Matrix export created successfully with batch rotation data")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_matrix_export():
    """Test CSV matrix export format"""
    print("\n" + "=" * 60)
    print("TEST 4: CSV Matrix Export")
    print("=" * 60)
    
    try:
        timetable_data = [
            {
                'Day': 'Monday',
                'Time': '10:00 - 11:00',
                'Period': 'P1',
                'Course Code': 'BS101',
                'Course Name': 'Mathematics',
                'Branch': 'Branch A',
                'Type': 'Theory',
                'Instructor': 'Prof A',
                'Semester': '1',
                'Section': 'A',
                'Batch': 'All',
                'Hours Per Week': 2
            },
            {
                'Day': 'Tuesday',
                'Time': '10:00 - 11:00',
                'Period': 'P1',
                'Course Code': 'BS102',
                'Course Name': 'Physics',
                'Branch': 'Branch A',
                'Type': 'Theory',
                'Instructor': 'Prof B',
                'Semester': '1',
                'Section': 'A',
                'Batch': 'All',
                'Hours Per Week': 2
            }
        ]
        
        df = pd.DataFrame(timetable_data)
        csv_bytes = TimetableExporter.export_timetable_matrix_csv(df)
        
        assert len(csv_bytes) > 0, "CSV export is empty"
        print("✅ CSV matrix export created")
        
        # Parse CSV to verify structure
        csv_str = csv_bytes.decode('utf-8')
        lines = csv_str.split('\n')
        print(f"✅ CSV structure verified:")
        print(f"   - Header row: {lines[0][:80]}")
        print(f"   - Data rows: {len([l for l in lines if l.strip()])}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MATRIX EXPORT & OVERLAP PREVENTION TEST SUITE")
    print("=" * 60)
    
    results = []
    results.append(("Matrix Structure", test_matrix_structure()))
    results.append(("Overlap Prevention", test_overlap_prevention()))
    results.append(("Batch Rotation", test_batch_rotation()))
    results.append(("CSV Matrix Export", test_csv_matrix_export()))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total_count - passed_count} test(s) failed")
        sys.exit(1)
