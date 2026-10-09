"""Read-only CVAT Cloud / GitHub snapshot collector. No QA metrics inferred."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Client:
    def __init__(self, base, token, org=None):
        self.base = base.rstrip('/') + '/'
        self.session = requests.Session()
        # Match requests' default Accept used by the successful manual CVAT call.
        self.session.headers.update(Authorization=f'Bearer {token}')
        self.org = org
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=['GET'], respect_retry_after_header=True,
                      raise_on_status=False)
        self.session.mount('https://', HTTPAdapter(max_retries=retry))

    def get(self, path, params=None):
        url = urljoin(self.base, path)
        if urlsplit(url).scheme != 'https' or urlsplit(url).netloc != urlsplit(self.base).netloc:
            raise ValueError('Unsafe API pagination URL')
        params = dict(params or {})
        if self.org is not None:
            params['org'] = self.org
        response = self.session.get(url, params=params, timeout=(10, 60), allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError(f'GET {urlsplit(url).path} returned HTTP {response.status_code}')
        return response

    def listing(self, path, params=None, github=False):
        rows, seen = [], set()
        while path:
            if path in seen:
                raise ValueError('Repeated pagination URL')
            seen.add(path)
            response = self.get(path, params)
            payload = response.json()
            if github:
                if not isinstance(payload, list):
                    raise ValueError('Expected GitHub list')
                rows.extend(payload)
                path = response.links.get('next', {}).get('url')
            else:
                if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
                    raise ValueError('Expected CVAT paginated results')
                rows.extend(payload['results'])
                path = payload.get('next')
            params = None
        return rows


def cvat_snapshot(client, task_id):
    task = client.get(f'api/tasks/{task_id}').json()
    jobs = client.listing('api/jobs', {'task_id': task_id, 'page_size': 100})
    labels = client.listing('api/labels', {'task_id': task_id, 'page_size': 100})
    issues = client.listing('api/issues', {'task_id': task_id, 'page_size': 100})
    comments = []
    for issue in issues:
        comments.extend(client.listing('api/comments', {'issue_id': issue['id'], 'page_size': 100}))
    annotations = []
    for job in jobs:
        try:
            data = client.get(f"api/jobs/{job['id']}/annotations/").json()
            if not isinstance(data, dict) or any(not isinstance(data.get(key, []), list)
                                                  for key in ('tags', 'shapes', 'tracks')):
                raise ValueError('Invalid annotation payload')
            annotations.append({'job_id': job['id'], 'status': 'success', 'data': data})
        except (requests.RequestException, RuntimeError, ValueError) as error:
            row = {'job_id': job['id'], 'status': 'failed', 'error_type': type(error).__name__}
            if isinstance(error, RuntimeError):
                row['error'] = str(error)
            annotations.append(row)
    return {'task': task, 'jobs': jobs, 'labels': labels, 'issues': issues,
            'comments': comments, 'annotations': annotations}


def github_snapshot(client, repo):
    root = f'repos/{repo}/'
    issues = client.listing(root + 'issues', {'state': 'all', 'per_page': 100}, github=True)
    issues = [row for row in issues if 'pull_request' not in row]
    labels = client.listing(root + 'labels', {'per_page': 100}, github=True)
    comments = []
    for issue in issues:
        comments.extend(client.listing(root + f"issues/{issue['number']}/comments",
                                       {'per_page': 100}, github=True))
    return {'issues': issues, 'labels': labels, 'comments': comments}


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['cvat', 'github', 'all'], default='cvat')
    parser.add_argument('--task-id', type=int, default=None)
    parser.add_argument('--repo', default=os.getenv('GITHUB_REPO'))
    parser.add_argument('--output', type=Path, default=Path('data/raw'))
    args = parser.parse_args()
    sources = ['cvat', 'github'] if args.source == 'all' else [args.source]
    for source in sources:
        token = os.getenv(f'{source.upper()}_TOKEN', '').strip()
        if source == 'cvat' and (token.startswith('your_') or token in {'PAT_CVAT_CUA_ONG', '<PAT của ông>'}):
            parser.error(f'Replace the example {source.upper()}_TOKEN in .env with a real token')
    task_id = args.task_id
    if 'cvat' in sources:
        if task_id is None:
            try:
                task_id = int(os.getenv('CVAT_TASK_ID', ''))
            except ValueError:
                parser.error('Set --task-id or CVAT_TASK_ID')
        if task_id <= 0 or not os.getenv('CVAT_TOKEN'):
            parser.error('Positive task ID and CVAT_TOKEN are required')
    if 'github' in sources:
        if not args.repo or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
            parser.error('Set --repo OWNER/REPO or GITHUB_REPO')
    now = datetime.now(timezone.utc)
    folder = args.output / now.strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True, exist_ok=False)
    manifest = {'schema_version': 1, 'started_at': now.isoformat(), 'sources': {}}
    for source in sources:
        started = datetime.now(timezone.utc).isoformat()
        scope = {'task_id': task_id, 'host': os.getenv('CVAT_HOST', 'https://app.cvat.ai'),
                 'org': os.getenv('CVAT_ORG')} if source == 'cvat' else {'repo': args.repo}
        try:
            if source == 'cvat':
                client = Client(scope['host'], os.environ['CVAT_TOKEN'], scope['org'])
                payload = cvat_snapshot(client, task_id)
            else:
                github_token = os.getenv('GITHUB_TOKEN', '').strip()
                if github_token.startswith('your_'):
                    github_token = ''
                client = Client('https://api.github.com', github_token)
                if not github_token:
                    client.session.headers.pop('Authorization', None)
                payload = github_snapshot(client, args.repo)
            write_json(folder / f'{source}.json', payload)
            result = {'status': 'success', 'file': f'{source}.json',
                      'counts': {key: len(value) if isinstance(value, list) else 1
                                 for key, value in payload.items()}}
        except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
            # Never persist response bodies, tokens, or request headers in logs.
            result = {'status': 'failed', 'error_type': type(error).__name__}
            if isinstance(error, RuntimeError):
                result['error'] = str(error)
        manifest['sources'][source] = dict(result, scope=scope, started_at=started,
                                          finished_at=datetime.now(timezone.utc).isoformat())
        write_json(folder / 'manifest.json', manifest)
    print(f'Snapshot: {folder}')
    return 1 if any(row['status'] == 'failed' for row in manifest['sources'].values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
