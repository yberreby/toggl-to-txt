#!/usr/bin/env python3
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import sys
from typing import Dict, List, Tuple, DefaultDict

Entry = Dict[str, str | timedelta]

def parse_duration(s: str) -> timedelta:
    h, m, s = map(int, s.split(':'))
    return timedelta(hours=h, minutes=m, seconds=s)

def fmt_time(time_str: str) -> str:
    return time_str[:5]

def fmt_dur(td: timedelta) -> str:
    total_sec = int(td.total_seconds())
    h, m = total_sec // 3600, (total_sec % 3600) // 60
    return f"{h}h {m}m" if h else f"{m}m"

def fmt_dur_long(td: timedelta) -> str:
    d, s = td.days, td.seconds
    h, m = s // 3600, (s % 3600) // 60
    parts = [(d, 'd'), (h, 'h'), (m, 'm')]
    return ' '.join(f"{v}{u}" for v, u in parts if v) or "0m"

def week_of(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"

def month_of(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.year}-{dt.month:02d}"

def load_entries(filename: str) -> List[Entry]:
    with open(filename, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            yield {
                'date': row['Start date'],
                'project': row['Project'],
                'desc': row['Description'] or "",
                'start': fmt_time(row['Start time']),
                'end': fmt_time(row['End time']),
                'duration': parse_duration(row['Duration'])
            }

def sum_durations(entries: List[Entry]) -> timedelta:
    return sum((e['duration'] for e in entries), timedelta())

def group_by_project(entries: List[Entry]) -> DefaultDict[str, timedelta]:
    by_project: DefaultDict[str, timedelta] = defaultdict(timedelta)
    for e in entries:
        by_project[e['project']] += e['duration']
    return by_project

def compute_stats(entries: List[Entry]) -> Tuple[timedelta, List[Tuple[str, timedelta]]]:
    total = sum_durations(entries)
    by_project = group_by_project(entries)
    sorted_projects = sorted(by_project.items(), key=lambda x: x[1], reverse=True)
    return total, sorted_projects

def merge_descriptions(current_desc: str, new_desc: str) -> str:
    if not current_desc and new_desc:
        return new_desc
    elif new_desc and new_desc not in current_desc:
        return f"{current_desc}; {new_desc}"
    return current_desc

def coalesce_consecutive(entries: List[Entry]) -> List[Entry]:
    if not entries:
        return []
    
    coalesced = []
    current = entries[0].copy()
    
    for e in entries[1:]:
        if e['project'] == current['project']:
            current['end'] = e['end']
            current['duration'] += e['duration']
            current['desc'] = merge_descriptions(current['desc'], e['desc'])
        else:
            coalesced.append(current)
            current = e.copy()
    
    coalesced.append(current)
    return coalesced

def truncate_desc(desc: str, max_len: int = 50) -> str:
    return desc[:max_len] + "..." if len(desc) > max_len else desc

def format_entry_line(entry: Entry) -> str:
    base = f"{entry['start']} - {entry['end']} ({fmt_dur(entry['duration']):>6}) | {entry['project']:<28}"
    if entry['desc']:
        return f"{base} | {entry['desc']}"
    return base

def format_project_stat(project: str, duration: timedelta, percentage: float) -> str:
    return f"{project:<35} {fmt_dur(duration):>8} ({percentage:5.1f}%)"

def format_project_stat_long(project: str, duration: timedelta, percentage: float) -> str:
    return f"{project:<35} {fmt_dur_long(duration):>12} ({percentage:5.1f}%)"

def calculate_percentage(part: timedelta, total: timedelta) -> float:
    return (part.total_seconds() / total.total_seconds()) * 100

def print_separator(char: str, width: int = 70) -> None:
    print(char * width)

def print_header(title: str, border_char: str = '=') -> None:
    print(f"\n{border_char*70}")
    print(title)
    print(f"{border_char*70}\n")

def print_daily_entries(entries: List[Entry]) -> None:
    coalesced = coalesce_consecutive(entries)
    for e in coalesced:
        print(format_entry_line(e))

def analyze_work_pattern(entries: List[Entry]) -> str:
    if not entries:
        return ""
    
    sessions = len(coalesce_consecutive(entries))
    return f" ({sessions} work blocks)"

def print_daily_stats(entries: List[Entry]) -> None:
    total, stats = compute_stats(entries)
    pattern = analyze_work_pattern(entries)
    
    print(f"\n{'-'*70}")
    print(f"Daily Total: {fmt_dur(total)}{pattern}")
    print(f"{'-'*70}")
    
    for proj, dur in stats:
        pct = calculate_percentage(dur, total)
        print(format_project_stat(proj, dur, pct))

def print_day_timeline(date: str, entries: List[Entry]) -> None:
    dt = datetime.strptime(date, "%Y-%m-%d")
    print_header(dt.strftime('%A, %B %d, %Y'))
    print_daily_entries(entries)
    print_daily_stats(entries)

def group_by_day(entries: List[Entry]) -> DefaultDict[str, List[Entry]]:
    by_day: DefaultDict[str, List[Entry]] = defaultdict(list)
    for e in entries:
        by_day[e['date']].append(e)
    return by_day

def print_week_days(entries: List[Entry]) -> None:
    by_day = group_by_day(entries)
    for date in sorted(by_day.keys()):
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_total = sum_durations(by_day[date])
        print(f"{dt.strftime('%a %b %d'):15} {fmt_dur(day_total):>8}")

def print_week_stats(entries: List[Entry], limit: int = 10) -> None:
    total, stats = compute_stats(entries)
    
    print(f"\n{'-'*35}")
    print(f"Week Total: {fmt_dur_long(total)}")
    print(f"{'-'*35}")
    
    for proj, dur in stats[:limit]:
        pct = calculate_percentage(dur, total)
        print(format_project_stat_long(proj, dur, pct))

def print_week_summary(week: str, entries: List[Entry]) -> None:
    print_header(f"WEEK {week}", '▓')
    print_week_days(entries)
    print_week_stats(entries)

def group_by_week(entries: List[Entry]) -> DefaultDict[str, List[Entry]]:
    by_week: DefaultDict[str, List[Entry]] = defaultdict(list)
    for e in entries:
        by_week[week_of(e['date'])].append(e)
    return by_week

def print_month_weeks(entries: List[Entry]) -> None:
    by_week = group_by_week(entries)
    for week in sorted(by_week.keys()):
        week_total = sum_durations(by_week[week])
        print(f"Week {week[5:]:10} {fmt_dur_long(week_total):>15}")

def average_per_day(total: timedelta, entries: List[Entry]) -> timedelta:
    unique_days = len(set(e['date'] for e in entries))
    return total / unique_days if unique_days > 0 else timedelta()

def print_month_stats(entries: List[Entry], limit: int = 7) -> None:
    total, stats = compute_stats(entries)
    avg = average_per_day(total, entries)
    
    print(f"\n{'-'*35}")
    print(f"Month Total: {fmt_dur_long(total)}")
    print(f"Average per day: {fmt_dur(avg)}")
    print(f"{'-'*35}")
    
    for proj, dur in stats[:limit]:
        pct = calculate_percentage(dur, total)
        print(format_project_stat_long(proj, dur, pct))

def print_month_summary(month: str, entries: List[Entry]) -> None:
    print_header(f"MONTH {month}", '█')
    print_month_weeks(entries)
    print_month_stats(entries)

def group_by_month(entries: List[Entry]) -> DefaultDict[str, List[Entry]]:
    by_month: DefaultDict[str, List[Entry]] = defaultdict(list)
    for e in entries:
        by_month[month_of(e['date'])].append(e)
    return by_month

def print_overall_summary(entries: List[Entry]) -> None:
    total, stats = compute_stats(entries)
    unique_days = len(set(e['date'] for e in entries))
    avg = average_per_day(total, entries)
    
    print_header(f"OVERALL SUMMARY ({unique_days} days)", '#')
    print(f"Total time tracked: {fmt_dur_long(total)}")
    print(f"Average per day: {fmt_dur(avg)}")
    print("\nTop Projects:")
    
    for proj, dur in stats[:15]:
        pct = calculate_percentage(dur, total)
        print(f"{proj:<40} {fmt_dur_long(dur):>15} ({pct:5.1f}%)")

def print_section_header(title: str) -> None:
    print(f"\n\n{'='*70}")
    print(title)
    print(f"{'='*70}")

def print_daily_timelines(entries: List[Entry]) -> None:
    by_day = group_by_day(entries)
    for date in sorted(by_day.keys()):
        print_day_timeline(date, by_day[date])

def print_weekly_summaries(entries: List[Entry]) -> None:
    print_section_header("WEEKLY SUMMARIES")
    by_week = group_by_week(entries)
    for week in sorted(by_week.keys()):
        print_week_summary(week, by_week[week])

def print_monthly_summaries(entries: List[Entry]) -> None:
    print_section_header("MONTHLY SUMMARIES")
    by_month = group_by_month(entries)
    for month in sorted(by_month.keys()):
        print_month_summary(month, by_month[month])

def main() -> None:
    filename = sys.argv[1] if len(sys.argv) > 1 else "Toggl_time_entries_2025-03-27_to_2025-06-24.csv"
    
    entries = list(load_entries(filename))
    
    print_daily_timelines(entries)
    print_weekly_summaries(entries)
    print_monthly_summaries(entries)
    print_overall_summary(entries)

if __name__ == "__main__":
    main()