#!/usr/bin/env python3
import pytest
from datetime import timedelta
from toggl_to_timeline import (
    parse_duration, fmt_dur, fmt_dur_long, week_of, month_of,
    merge_descriptions, coalesce_consecutive, calculate_percentage,
    sum_durations, group_by_project, fmt_time
)

def test_parse_duration():
    assert parse_duration("01:30:45") == timedelta(hours=1, minutes=30, seconds=45)
    assert parse_duration("00:15:00") == timedelta(minutes=15)
    assert parse_duration("10:00:00") == timedelta(hours=10)

def test_fmt_dur():
    assert fmt_dur(timedelta(hours=2, minutes=30)) == "2h 30m"
    assert fmt_dur(timedelta(minutes=45)) == "45m"
    assert fmt_dur(timedelta(hours=1)) == "1h 0m"

def test_fmt_dur_long():
    assert fmt_dur_long(timedelta(days=2, hours=3, minutes=15)) == "2d 3h 15m"
    assert fmt_dur_long(timedelta(hours=5, minutes=30)) == "5h 30m"
    assert fmt_dur_long(timedelta(minutes=20)) == "20m"
    assert fmt_dur_long(timedelta()) == "0m"

def test_week_of():
    assert week_of("2025-03-27") == "2025-W13"
    assert week_of("2025-01-01") == "2025-W01"

def test_month_of():
    assert month_of("2025-03-27") == "2025-03"
    assert month_of("2025-12-31") == "2025-12"

def test_fmt_time():
    assert fmt_time("14:30:00") == "14:30"
    assert fmt_time("09:05:30") == "09:05"

def test_merge_descriptions():
    assert merge_descriptions("", "new task") == "new task"
    assert merge_descriptions("existing", "new") == "existing; new"
    assert merge_descriptions("task", "task") == "task"
    assert merge_descriptions("task1; task2", "task2") == "task1; task2"

def test_coalesce_consecutive():
    entries = [
        {'project': 'A', 'start': '09:00', 'end': '10:00', 'duration': timedelta(hours=1), 'desc': 'task1'},
        {'project': 'A', 'start': '10:00', 'end': '11:00', 'duration': timedelta(hours=1), 'desc': 'task2'},
        {'project': 'B', 'start': '11:00', 'end': '12:00', 'duration': timedelta(hours=1), 'desc': ''},
    ]
    result = coalesce_consecutive(entries)
    
    assert len(result) == 2
    assert result[0]['project'] == 'A'
    assert result[0]['start'] == '09:00'
    assert result[0]['end'] == '11:00'
    assert result[0]['duration'] == timedelta(hours=2)
    assert result[0]['desc'] == 'task1; task2'
    
    assert result[1]['project'] == 'B'

def test_coalesce_empty():
    assert coalesce_consecutive([]) == []

def test_calculate_percentage():
    assert calculate_percentage(timedelta(hours=1), timedelta(hours=4)) == 25.0
    assert calculate_percentage(timedelta(minutes=30), timedelta(hours=1)) == 50.0

def test_sum_durations():
    entries = [
        {'duration': timedelta(hours=1)},
        {'duration': timedelta(minutes=30)},
        {'duration': timedelta(hours=2)},
    ]
    assert sum_durations(entries) == timedelta(hours=3, minutes=30)

def test_group_by_project():
    entries = [
        {'project': 'A', 'duration': timedelta(hours=1)},
        {'project': 'B', 'duration': timedelta(hours=2)},
        {'project': 'A', 'duration': timedelta(hours=1.5)},
    ]
    grouped = group_by_project(entries)
    
    assert grouped['A'] == timedelta(hours=2.5)
    assert grouped['B'] == timedelta(hours=2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])