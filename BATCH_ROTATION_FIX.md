# BATCH ROTATION FIX - SUMMARY

## Problem Fixed

**Before:** Labs were being spread across different days
- Monday: Lab1 at 15:30-17:00
- Tuesday: Lab2 at 15:30-17:00 (different lab)
- Wednesday: Lab3 at 15:30-17:00 (different lab)
- Thursday: Lab4 at 15:30-17:00 (different lab)

**After:** All labs at the same time slot are scheduled on EACH day with rotating batches
- Monday: Lab1 (B1), Lab2 (B2), Lab3 (B3) at 15:30-17:00
- Tuesday: Lab1 (B2), Lab2 (B3), Lab3 (B1) at 15:30-17:00
- Wednesday: Lab1 (B3), Lab2 (B1), Lab3 (B2) at 15:30-17:00
- Thursday: Lab1 (B1), Lab2 (B2), Lab3 (B3) at 15:30-17:00
- Friday: Lab1 (B2), Lab2 (B3), Lab3 (B1) at 15:30-17:00

## What Was Changed

### File: app.py (Lines 361-447)

**Modified Schedule Generation Logic:**

1. **For LAB courses (NEW LOGIC):**
   - Find a suitable time slot by checking all days
   - Once a slot is found, assign the SAME lab to ALL 5 days at that time slot
   - Creates duplicate Lecture objects for each day
   - Each day's lab gets a batch number later

2. **For THEORY courses (ORIGINAL LOGIC):**
   - Find first available day and assign (unchanged)
   - Theory lectures stay on single days

**Key Code Change:**
```python
if course_data['type'] == 'Lab':
    # Find best time slot
    # Assign to ALL days at that slot
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        lecture = Lecture(...)
        generator.assign_lecture(lecture, day, slot_start, slot_end)
else:
    # Theory: assign to first available day (original)
```

## Batch Rotation Formula

Once labs are scheduled on each day at the same time slot, the `apply_rotating_batch_assignment()` function applies:

```
batch_number = ((course_index + day_offset) % batch_size) + 1
```

Where:
- `course_index` = Global position of course in sorted order (0, 1, 2...)
- `day_offset` = 0 (Mon), 1 (Tue), 2 (Wed), 3 (Thu), 4 (Fri)
- `batch_size` = Number of batches (typically 3 or 4)

## Example with 3 Labs, Batch Size 3

Labs: CS405 (DB), CS406 (DS), CS407 (CN)

### Course Indices:
- CS405 = index 0
- CS406 = index 1  
- CS407 = index 2

### Rotation Table:

| Day       | Offset | CS405 Calc      | CS405 Batch | CS406 Calc      | CS406 Batch | CS407 Calc      | CS407 Batch |
|-----------|--------|-----------------|-------------|-----------------|-------------|-----------------|-------------|
| Monday    | 0      | (0+0)%3+1 = 1   | 1           | (1+0)%3+1 = 2   | 2           | (2+0)%3+1 = 3   | 3           |
| Tuesday   | 1      | (0+1)%3+1 = 2   | 2           | (1+1)%3+1 = 3   | 3           | (2+1)%3+1 = 1   | 1           |
| Wednesday | 2      | (0+2)%3+1 = 3   | 3           | (1+2)%3+1 = 1   | 1           | (2+2)%3+1 = 2   | 2           |
| Thursday  | 3      | (0+3)%3+1 = 1   | 1           | (1+3)%3+1 = 2   | 2           | (2+3)%3+1 = 3   | 3           |
| Friday    | 4      | (0+4)%3+1 = 2   | 2           | (1+4)%3+1 = 3   | 3           | (2+4)%3+1 = 1   | 1           |

## How to Test

1. **Initialize Schedule** (Sidebar):
   - Set college hours
   - Set recess times
   - Choose "Flexible custom timing" or "Reference period layout"
   - Click "Initialize Schedule"

2. **Add Lab Courses** (Tab 1: Add Classes):
   - Add 3-4 lab courses for the SAME semester
   - Example:
     - Course Code: CS405, Name: Database Lab, Type: **Lab**
     - Course Code: CS406, Name: Data Science Lab, Type: **Lab**
     - Course Code: CS407, Name: Networks Lab, Type: **Lab**
   - Set batch size (e.g., 3 batches for 3 courses)

3. **Generate Schedule**:
   - Click "🚀 GENERATE SCHEDULE"
   - View the timetable

4. **Verify Output**:
   - All 3 labs should appear on EACH day at the same time slot
   - Batch numbers should rotate following the pattern shown above
   - No batch should meet the same lab on consecutive days

## Files Modified

- ✅ app.py (schedule generation logic)
- ✅ app.py (batch rotation function - from previous fix)

## Verification

✅ Code compiles without errors
✅ Schedule generation assigns labs to all days at same time
✅ Batch rotation applies correct rotation formula
✅ Instructor conflicts are checked per day
✅ Theory courses maintain original behavior (single day assignment)
