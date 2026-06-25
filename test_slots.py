from schedule_generator import ScheduleGenerator

g = ScheduleGenerator('08:30','17:00','10:30','10:45','13:00','14:00', use_reference_periods=False)
print('Generated lab slots (1.5h) Monday:')
print(g.get_available_slots('Monday',1.5, session_type='Lab'))
print('\nGenerated theory slots (1h) Monday:')
print(g.get_available_slots('Monday',1.0, session_type='Theory')[:10])
