# task_utils.py (enhanced)
from typing import List, Dict


def identify_parallel_groups(tasks: List[Dict]) -> List[List[str]]:
    graph = {t['id']: set() for t in tasks}
    for t in tasks:
        for dep in t.get('dependencies', []):
            if dep['is_blocking']:
                graph[t['id']].add(dep['task_id'])

    visited = set()
    current_group = set()
    groups = []

    def visit(task_id):
        if task_id in visited:
            return
        visited.add(task_id)
        if not graph[task_id] & visited:
            current_group.add(task_id)
        else:
            if current_group:
                groups.append(list(current_group))
                current_group.clear()
            current_group.add(task_id)
        for dt in tasks:
            if dt['id'] not in visited:
                if any(dep['task_id'] == task_id for dep in dt.get('dependencies', [])):
                    visit(dt['id'])

    for t in tasks:
        if t['id'] not in visited:
            visit(t['id'])

    if current_group:
        groups.append(list(current_group))
    return groups


def calculate_critical_path(tasks: List[Dict]) -> List[str]:
    times = {t['id']: 0 for t in tasks}
    for t in tasks:
        duration = t['expected_duration']
        for dep in t.get('dependencies', []):
            if dep['is_blocking']:
                times[t['id']] = max(times[t['id']], times[dep['task_id']] + duration)

    critical_path = []
    current = max(times.items(), key=lambda x: x[1])[0] if times else None
    while current:
        critical_path.append(current)
        max_dep, max_time = None, -1
        for dt in tasks:
            if dt['id'] == current:
                for dep in dt.get('dependencies', []):
                    if dep['is_blocking'] and times[dep['task_id']] > max_time:
                        max_time = times[dep['task_id']]
                        max_dep = dep['task_id']
        current = max_dep
    return list(reversed(critical_path))
