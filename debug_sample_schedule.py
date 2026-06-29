import pandas as pd
import math
from schedule_generator import ScheduleGenerator, Lecture

# load sample courses
df = pd.read_csv('sample_courses_up.csv')
config = {
    'morning_start': '08:30',
    'morning_end': '17:00',
    'short_recess_start': '10:30',
    'short_recess_end': '10:45',
    'long_recess_start': '13:00',
    'long_recess_end': '14:00',
    'use_reference_periods': True,
    'include_saturday': True
}

gens = {}
for sem in df['semester'].unique():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if config['include_saturday']:
        days.append('Saturday')
    gens[sem] = ScheduleGenerator(
        config['morning_start'], config['morning_end'],
        config['short_recess_start'], config['short_recess_end'],
        config['long_recess_start'], config['long_recess_end'],
        use_reference_periods=config['use_reference_periods'],
        days=days
    )

pending = []
for _, r in df.iterrows():
    stype = r['session_type']
    if isinstance(stype, str):
        stype = stype.strip().lower()
    if stype == 'project':
        stype = 'lab'
    stype = 'Lab' if stype == 'lab' else 'Theory'
    duration = 1.0
    batch = 'All'
    if stype == 'Lab':
        batch_size = int(r['batch_size']) if not pd.isna(r['batch_size']) else 4
        batch = f'1-{batch_size}'
    pending.append({
        'code': r['course_code'],
        'name': r['course_name'],
        'instructor': r['instructor'],
        'type': stype,
        'semester': r['semester'],
        'section': r['section'],
        'branch': r['branch'],
        'duration': duration,
        'batch': batch,
        'hours_per_week': float(r['hours_per_week'])
    })

# schedule labs first (use course-based offset to spread afternoon slots)
for c in [x for x in pending if x['type'] == 'Lab']:
    g = gens[c['semester']]
    num_sessions = max(1, math.ceil(c['hours_per_week'] / c['duration']))
    s = 0
    for day_index, day in enumerate(g.days):
        if s >= num_sessions:
            break
        lecture_template = Lecture(
            c['code'], c['name'], c['instructor'], c['type'], c['semester'], c['section'], c['branch'],
            duration=c['duration'], batch=c['batch'], hours_per_week=c['hours_per_week']
        )
        avail = g.get_available_slots(day, c['duration'], session_type='Lab', lecture=lecture_template)
        if not avail:
            continue

        # choose offset based on course code to vary preferred slot
        offset = sum(ord(ch) for ch in str(c['code'])) % len(avail)
        idx = (day_index + offset) % len(avail)

        assigned = False
        for i in range(len(avail)):
            s_idx = (idx + i) % len(avail)
            s_start, s_end = avail[s_idx]
            lect = Lecture(c['code'], c['name'], c['instructor'], c['type'], c['semester'], c['section'], c['branch'], duration=c['duration'], batch=c['batch'], hours_per_week=c['hours_per_week'])
            if g.assign_lecture(lect, day, s_start, s_end, allow_parallel_labs=True):
                s += 1
                assigned = True
                break
        if assigned:
            continue
    print('LAB', c['code'], s, '/', num_sessions)

# schedule theories (use rotating slot selection to avoid repeating the same period)
for c in sorted([x for x in pending if x['type'] == 'Theory'], key=lambda z: math.ceil(z['hours_per_week'] / z['duration']), reverse=True):
    g = gens[c['semester']]
    num_sessions = max(1, math.ceil(c['hours_per_week'] / c['duration']))
    s = 0
    used_day_slots = set()

    # Attempt multiple passes over the week until all sessions scheduled or no progress
    max_cycles = max(3, math.ceil(num_sessions / max(1, len(g.days)) ) + 2)
    for cycle in range(max_cycles):
        progress = False
        for day_index, day in enumerate(g.days):
            if s >= num_sessions:
                break
            avail = g.get_available_slots(day, c['duration'])
            if not avail:
                continue

            idx = (day_index + s) % len(avail)
            start_slot, end_slot = avail[idx]
            slot_key = (day, start_slot, end_slot)

            if slot_key in used_day_slots:
                found = False
                for i in range(len(avail)):
                    idx2 = (idx + i) % len(avail)
                    s2, e2 = avail[idx2]
                    if (day, s2, e2) not in used_day_slots:
                        start_slot, end_slot = s2, e2
                        slot_key = (day, start_slot, end_slot)
                        found = True
                        break
                if not found:
                    continue

            lect = Lecture(c['code'], c['name'], c['instructor'], c['type'], c['semester'], c['section'], c['branch'], duration=c['duration'], batch=c['batch'], hours_per_week=c['hours_per_week'])
            if g.assign_lecture(lect, day, start_slot, end_slot):
                s += 1
                used_day_slots.add(slot_key)
                progress = True
        if s >= num_sessions:
            break
        if not progress:
            break
    print('THEORY', c['code'], s, '/', num_sessions)

# inspect 4th sem timetable
print('\n4th sem timetable entries', len(gens['4th'].timetable))
for row in gens['4th'].timetable:
    print(row)