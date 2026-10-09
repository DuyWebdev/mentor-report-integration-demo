"""Collect both sources and verify explicit issue references against CVAT."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re

import requests
from dotenv import load_dotenv

from collect import Client, cvat_snapshot, github_snapshot, write_json
from verify_link import extract_ids


def link_issues(issues, cvat, jobs):
    cache = {job['id']: job for job in jobs}
    links = []
    for issue in issues:
        row = {'github_issue': issue['number'], 'github_url': issue['html_url'],
               'github_issue_updated_at': issue.get('updated_at')}
        body = issue.get('body') or ''
        if not re.search(r'^CVAT (task|job) ID:', body, re.MULTILINE):
            links.append(dict(row, status='unlinked'))
            continue
        try:
            task_id, job_id = extract_ids(body)
        except ValueError:
            links.append(dict(row, status='invalid_reference'))
            continue
        row.update(cvat_task_id=task_id, cvat_job_id=job_id)
        try:
            if job_id not in cache:
                cache[job_id] = cvat.get(f'api/jobs/{job_id}').json()
            actual = cache[job_id].get('task_id')
            if not isinstance(actual, int):
                raise ValueError('Missing task_id')
            row.update(actual_cvat_task_id=actual, relationship_verified=actual == task_id,
                       status='verified' if actual == task_id else 'mismatch')
        except (requests.RequestException, RuntimeError, ValueError, KeyError) as error:
            row.update(status='verification_failed', error_type=type(error).__name__)
        links.append(row)
    return links


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', type=int, default=None)
    parser.add_argument('--repo', default=os.getenv('GITHUB_REPO'))
    parser.add_argument('--session', help='Tên phiên mentor hoặc kỳ báo cáo')
    args = parser.parse_args()
    try:
        task_id = args.task_id or int(os.getenv('CVAT_TASK_ID', ''))
    except ValueError:
        parser.error('Set CVAT_TASK_ID or --task-id')
    token = os.getenv('CVAT_TOKEN', '').strip()
    if task_id <= 0 or not token or token.startswith('your_'):
        parser.error('Set a positive task ID and real CVAT_TOKEN in .env')
    if not args.repo or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Set GITHUB_REPO or --repo OWNER/REPO')
    github_token = os.getenv('GITHUB_TOKEN', '').strip()
    if github_token.startswith('your_'):
        github_token = ''
    github = Client('https://api.github.com', github_token)
    if not github_token:
        github.session.headers.pop('Authorization', None)
    cvat = Client(os.getenv('CVAT_HOST', 'https://app.cvat.ai'), token, os.getenv('CVAT_ORG'))
    started = datetime.now(timezone.utc)
    folder = Path('data/raw') / started.strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    manifest = {'schema_version': 1, 'started_at': started.isoformat(),
                'scope': {'task_id': task_id, 'repo': args.repo, 'cvat_host': cvat.base,
                          'org': os.getenv('CVAT_ORG')}, 'sources': {}}
    payloads = {}
    for name, fetch in [('cvat', lambda: cvat_snapshot(cvat, task_id)),
                        ('github', lambda: github_snapshot(github, args.repo))]:
        source_start = datetime.now(timezone.utc).isoformat()
        try:
            data = fetch()
            write_json(folder / f'{name}.json', data)
            payloads[name] = data
            result = {'status': 'success', 'file': f'{name}.json',
                      'counts': {key: len(value) if isinstance(value, list) else 1
                                 for key, value in data.items()}}
            if name == 'cvat':
                result['annotations'] = {'successful_jobs': sum(r['status'] == 'success' for r in data['annotations']),
                                         'failed_jobs': sum(r['status'] == 'failed' for r in data['annotations'])}
        except (requests.RequestException, RuntimeError, ValueError, KeyError) as error:
            result = {'status': 'failed', 'error_type': type(error).__name__}
            if isinstance(error, RuntimeError):
                result['error'] = str(error)
        manifest['sources'][name] = dict(result, started_at=source_start,
                                        finished_at=datetime.now(timezone.utc).isoformat())
        print(f'{name}: {result["status"]}')
        write_json(folder / 'manifest.json', manifest)
    if 'github' in payloads:
        links = link_issues(payloads['github']['issues'], cvat,
                            payloads.get('cvat', {}).get('jobs', []))
        write_json(folder / 'links.json', links)
        counts = {status: sum(row['status'] == status for row in links)
                  for status in ('verified', 'mismatch', 'unlinked', 'invalid_reference', 'verification_failed')}
        manifest['links'] = {'file': 'links.json', 'counts': counts}
        print('Links:', counts)
    else:
        manifest['links'] = {'status': 'skipped', 'reason': 'github source failed'}
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    write_json(folder / 'manifest.json', manifest)
    from report import generate
    generate(folder, args.session)
    print('Report:', folder / 'MENTOR_REPORT_DRAFT.md')
    print('Saved:', folder)
    failed = any(row['status'] == 'failed' for row in manifest['sources'].values())
    failed = failed or bool(manifest['sources'].get('cvat', {}).get('annotations', {}).get('failed_jobs', 0))
    problems = any(manifest.get('links', {}).get('counts', {}).get(key, 0)
                   for key in ('mismatch', 'invalid_reference', 'verification_failed'))
    return 1 if failed or problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
