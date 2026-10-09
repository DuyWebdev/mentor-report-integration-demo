"""Verify the CVAT task/job references in one public GitHub issue."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from dotenv import load_dotenv

from collect import Client


def extract_ids(body):
    ids = {}
    for kind in ('task', 'job'):
        matches = re.findall(rf'^CVAT {kind} ID:[ \t]*(\d+)[ \t]*\r?$',
                             body or '', re.MULTILINE)
        if len(matches) != 1 or int(matches[0]) <= 0:
            raise ValueError(f'Issue must contain exactly one positive CVAT {kind} ID')
        ids[kind] = int(matches[0])
    return ids['task'], ids['job']


def verify(github, cvat, repo, number):
    issue = github.get(f'repos/{repo}/issues/{number}').json()
    if 'pull_request' in issue:
        raise ValueError('Expected an issue, received a pull request')
    task_id, job_id = extract_ids(issue.get('body'))
    job = cvat.get(f'api/jobs/{job_id}').json()
    if not isinstance(job.get('task_id'), int):
        raise ValueError('CVAT response is missing an integer task_id')
    return {
        'github_repo': repo, 'github_issue': issue['number'],
        'github_url': issue['html_url'], 'github_issue_updated_at': issue.get('updated_at'),
        'cvat_task_id': task_id, 'cvat_job_id': job_id,
        'actual_cvat_task_id': job['task_id'],
        'relationship_verified': job['task_id'] == task_id,
        'verified_at': datetime.now(timezone.utc).isoformat(),
    }


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default=os.getenv('GITHUB_REPO'))
    parser.add_argument('--issue', type=int, required=True)
    parser.add_argument('--output', type=Path, default=Path('data/raw/verified-links'))
    args = parser.parse_args()
    if not args.repo or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Set GITHUB_REPO or --repo OWNER/REPO')
    if args.issue <= 0:
        parser.error('--issue must be positive')
    token = os.getenv('CVAT_TOKEN', '').strip()
    if not token or token.startswith('your_'):
        parser.error('Set a real CVAT_TOKEN in .env')
    github = Client('https://api.github.com', '')
    # Public GitHub reads do not require authentication.
    github.session.headers.pop('Authorization', None)
    cvat = Client(os.getenv('CVAT_HOST', 'https://app.cvat.ai'), token,
                  os.getenv('CVAT_ORG'))
    try:
        result = verify(github, cvat, args.repo, args.issue)
    except (RuntimeError, ValueError, KeyError) as error:
        print(f'Verification failed: {error}')
        return 1
    except Exception as error:
        # Do not print request details or secrets.
        print(f'Verification failed: {type(error).__name__}')
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Matches issue:', result['relationship_verified'])
    print('Saved:', output)
    return 0 if result['relationship_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
