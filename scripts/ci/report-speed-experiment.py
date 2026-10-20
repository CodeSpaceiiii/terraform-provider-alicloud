#!/usr/bin/env python3
"""Report an experiment run: python3 scripts/ci/report-speed-experiment.py RUN_ID.

Uses the active gh identity. Reports queue and execution separately, without
claiming that a faster failed/cancelled check is a successful optimization.
"""
import datetime as dt
import json
import subprocess
import sys

REPO = 'CodeSpaceiiii/terraform-provider-alicloud'


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def instant(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


def main():
    run_id = int(sys.argv[1])
    run = api(f'repos/{REPO}/actions/runs/{run_id}')
    jobs = []
    page = 1
    while True:
        batch = api(f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100&page={page}')['jobs']
        jobs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    rows = []
    for job in jobs:
        created, started, ended = map(instant, [job.get('created_at'), job.get('started_at'), job.get('completed_at')])
        rows.append({
            'name': job['name'], 'status': job['status'], 'conclusion': job['conclusion'],
            'queueSeconds': round((started - created).total_seconds(), 1) if created and started else None,
            'executionSeconds': round((ended - started).total_seconds(), 1) if started and ended else None,
            'url': job['html_url'],
            'steps': [{'name': s['name'], 'conclusion': s.get('conclusion'),
                       'seconds': round((instant(s['completed_at']) - instant(s['started_at'])).total_seconds(), 1)
                       if s.get('started_at') and s.get('completed_at') else None}
                      for s in job.get('steps', [])],
        })
    print(json.dumps({'runUrl': run['html_url'], 'status': run['status'],
                      'conclusion': run['conclusion'], 'jobs': rows}, indent=2))


if __name__ == '__main__':
    main()
