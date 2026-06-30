import importlib.util
import pathlib
import shutil
import sys
import os

root = pathlib.Path(r'D:\Time_table')
for pycache in root.rglob('__pycache__'):
    shutil.rmtree(pycache)

# Load schedule_generator from the workspace file fresh.
spec_schedule = importlib.util.spec_from_file_location('schedule_generator', root / 'schedule_generator.py')
schedule_module = importlib.util.module_from_spec(spec_schedule)
spec_schedule.loader.exec_module(schedule_module)
print('normalize', schedule_module.normalize_session_type('rotation'))

# Load export_handler fresh.
spec_export = importlib.util.spec_from_file_location('export_handler', root / 'export_handler.py')
export_module = importlib.util.module_from_spec(spec_export)
spec_export.loader.exec_module(export_module)

# Run tests.
import test_scheduler_rules as t
print('test 1', t.test_normalize_session_type_rotation_is_treated_as_theory())
print('test 2', t.test_export_matrix_includes_course_name_and_filters_out_of_config_slots())

# Verify overlap prevention.
from schedule_generator import ScheduleGenerator, Lecture

g = ScheduleGenerator('08:30','17:00','10:30','10:45','13:00','14:00', use_reference_periods=False)
lec1 = Lecture('C1','Course 1','Prof A','Theory','4th','A', duration=1.0)
lec2 = Lecture('C2','Course 2','Prof A','Theory','4th','A', duration=1.0)
print('overlap1', g.assign_lecture(lec1, 'Monday', '09:00', '10:00'))
print('overlap2', g.assign_lecture(lec2, 'Monday', '09:30', '10:30'))

# Verify lab batch rotation by loading app.py fresh.
spec_app = importlib.util.spec_from_file_location('app', root / 'app.py')
app_module = importlib.util.module_from_spec(spec_app)
spec_app.loader.exec_module(app_module)
rows = [
    {'Day':'Monday','Time':'09:00 - 10:00','Course Code':'LAB1','Course Name':'A','Type':'Lab','Semester':'4th','Batch':'All'},
    {'Day':'Monday','Time':'09:00 - 10:00','Course Code':'LAB2','Course Name':'B','Type':'Lab','Semester':'4th','Batch':'All'},
    {'Day':'Tuesday','Time':'09:00 - 10:00','Course Code':'LAB1','Course Name':'A','Type':'Lab','Semester':'4th','Batch':'All'},
    {'Day':'Tuesday','Time':'09:00 - 10:00','Course Code':'LAB2','Course Name':'B','Type':'Lab','Semester':'4th','Batch':'All'},
]
out = app_module.apply_rotating_batch_assignment(rows, {'4th': 3})
print('batches', [r['Batch'] for r in out])
