from schedule_generator import ScheduleGenerator

def print_slots(use_reference_periods):
    print('use_reference_periods=', use_reference_periods)
    g = ScheduleGenerator('08:30','17:00','10:30','10:45','13:00','14:00',use_reference_periods=use_reference_periods)
    print('theory slots sample:', g.get_available_slots('Monday',1.0,session_type='Theory')[:10])
    print('lab slots sample:', g.get_available_slots('Monday',1.0,session_type='Lab')[:10])
    print('---')

print_slots(False)
print_slots(True)
