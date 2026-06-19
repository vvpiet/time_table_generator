# Engineering College Timetable Generator

A comprehensive Streamlit web application for generating non-overlapping college timetables with conflict detection, designed specifically for engineering colleges.

## Features

✨ **Core Features:**
- ✅ **Non-overlapping Schedule Generation**: Advanced algorithm ensures no time conflicts between classes
- 📚 **Theory & Lab Sessions**: 
  - Theory lectures: 1 hour duration
  - Lab sessions: 1.5 hours duration
- ⏰ **Customizable Timings**:
  - Morning start and end times
  - Short recess timing
  - Long recess timing
- 📊 **Multiple Export Formats**:
  - CSV format for spreadsheets
  - Word format for documentation
  - Day-wise organized Word documents
- 👨‍🏫 **Instructor Schedules**: View individual instructor's schedule
- 📈 **Analytics Dashboard**: 
  - Classes by day/type/semester
  - Instructor load distribution
- 🎨 **User-friendly Interface**: Intuitive Streamlit-based UI

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd Time_table
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On macOS/Linux
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Step-by-Step Usage Guide

#### 1. **Configure Schedule (Sidebar)**
   - Set morning start time (e.g., 08:30 AM)
   - Set morning end time (e.g., 5:00 PM)
   - Set short recess timing (e.g., 10:30 AM - 10:45 AM)
   - Set long recess timing (e.g., 1:00 PM - 2:00 PM)
   - Click "Initialize Schedule"

#### 2. **Add Classes (Tab 1)**
   - Fill in course details:
     - Course Code (e.g., CS101)
     - Course Name (e.g., Data Structures)
     - Instructor Name
     - Semester (1st - 8th)
     - Section (A, B, C, D)
   - Select session type:
     - Theory (1 hour)
     - Lab (1.5 hours)
   - Choose day and available time slot
   - Click "Add Class to Timetable"

#### 3. **View Timetable (Tab 2)**
   - See complete timetable
   - View day-wise breakdown
   - Check quick statistics

#### 4. **Check Instructor Schedule (Tab 3)**
   - Select an instructor
   - View their complete schedule

#### 5. **View Analytics (Tab 4)**
   - Visual charts for:
     - Classes distribution by day
     - Theory vs Lab ratio
     - Semester-wise distribution
     - Instructor workload

#### 6. **Export Timetable (Tab 5)**
   - Download complete timetable in CSV or Word format
   - Export day-wise organized schedules
   - Export individual instructor schedules

## Project Structure

```
Time_table/
├── app.py                  # Main Streamlit application
├── schedule_generator.py   # Core scheduling logic
├── export_handler.py       # CSV and Word export functionality
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## File Descriptions

### `app.py`
Main Streamlit application with UI components including:
- Configuration sidebar for time settings
- Add Classes tab for input
- View Timetable with day-wise breakdown
- Instructor Schedule viewer
- Analytics dashboard
- Export functionality

### `schedule_generator.py`
Core scheduling engine:
- `TimeSlot`: Class for managing time slots
- `Lecture`: Class representing a course/lab session
- `ScheduleGenerator`: Main algorithm for conflict-free scheduling
- Methods for finding available slots, assigning lectures, and retrieving schedules

### `export_handler.py`
Export utilities:
- CSV export using pandas
- Word document generation using python-docx
- Formatted tables and headers
- Day-wise organized exports

## Dependencies

- **streamlit** (1.28.1): Web application framework
- **pandas** (2.0.3): Data manipulation and CSV handling
- **python-docx** (0.8.11): Word document generation
- **openpyxl** (3.1.2): Excel support (for Word generation)

## Algorithm Details

### Conflict Detection
The scheduler uses a time-slot comparison algorithm:
1. Maintains occupied slots for each day
2. When adding a new lecture, checks against existing occupancy
3. Avoids scheduling during recess periods
4. Returns available slots that fit the duration

### Available Slots Finding
- Iterates through the college hours in 30-minute increments
- Skips recess periods automatically
- Returns slots that don't overlap with existing classes
- Respects lecture duration (1 hour for theory, 1.5 hours for lab)

## Features in Detail

### Non-overlapping Schedule
- ✅ Prevents double-booking of instructors
- ✅ Prevents room conflicts (when implemented)
- ✅ Respects break timings
- ✅ Supports variable lecture durations

### Export Capabilities
- **CSV Format**: 
  - Easy to import into Excel
  - Includes all scheduling details
  
- **Word Format**: 
  - Professionally formatted tables
  - Black header with white text
  - Complete schedule in one document
  - Option for day-wise organization

## Configuration Examples

### Example 1: Standard Engineering College Schedule
```
Morning: 08:30 AM - 05:00 PM
Short Recess: 10:30 AM - 10:45 AM (15 minutes)
Long Recess: 01:00 PM - 02:00 PM (60 minutes)
```

### Example 2: Early Morning Schedule
```
Morning: 06:30 AM - 03:30 PM
Short Recess: 09:00 AM - 09:15 AM
Long Recess: 11:30 AM - 12:15 PM
```

## Troubleshooting

### Issue: "No available slots for this duration"
**Solution**: 
- Check if the selected day already has many classes
- Reduce duration or adjust recess timings
- Try a different day

### Issue: Export not working
**Solution**:
- Ensure at least one class is added
- Check if all required libraries are installed
- Try reinstalling python-docx: `pip install --upgrade python-docx`

### Issue: App won't start
**Solution**:
- Verify Python version (3.8+)
- Reinstall dependencies: `pip install -r requirements.txt`
- Check if port 8501 is not in use

## Future Enhancements

Potential features for future versions:
- 🔐 Room/Hall scheduling
- 👥 Student batch scheduling
- 🔄 Automatic conflict resolution
- 📱 Mobile-responsive design
- 🔔 Notification system
- 🗂️ Import schedules from CSV
- 🎨 Theme customization
- 📧 Email schedule to instructors

## Support & Contribution

For bugs, feature requests, or contributions, please follow these steps:
1. Document the issue clearly
2. Provide example inputs that reproduce the problem
3. Submit with relevant details

## License

This project is open source and available for educational and institutional use.

## Author

Engineering College Timetable Generator
Version 1.0

---

**Happy Scheduling! 📚✨**
