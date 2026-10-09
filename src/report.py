"""Normalize a snapshot and render the four-section mentor draft offline."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

from collect import write_json


def annotation_summary(cvat):
    records = (cvat or {}).get('annotations')
    if records is None:
        return {'status': 'unavailable', 'reason': 'Snapshot chưa thu thập annotations.',
                'jobs': [], 'totals': None, 'by_label': []}
    labels = {label['id']: label.get('name') for label in cvat.get('labels', [])}
    totals = {'shapes': 0, 'tracks': 0, 'tags': 0, 'track_shape_records': 0}
    by_label, jobs = {}, []
    failed = False
    for record in records:
        if record['status'] != 'success':
            failed = True
            jobs.append({'job_id': record['job_id'], 'status': 'failed', 'counts': None})
            continue
        data = record['data']
        counts = {key: len(data.get(key, [])) for key in ('shapes', 'tracks', 'tags')}
        counts['track_shape_records'] = sum(len(track.get('shapes', [])) for track in data.get('tracks', []))
        for key in totals:
            totals[key] += counts[key]
        for kind in ('shapes', 'tracks', 'tags'):
            for obj in data.get(kind, []):
                label_id = obj.get('label_id')
                if label_id not in by_label:
                    by_label[label_id] = {'label_id': label_id, 'label_name': labels.get(label_id),
                                          'shapes': 0, 'tracks': 0, 'tags': 0}
                by_label[label_id][kind] += 1
        jobs.append({'job_id': record['job_id'], 'status': 'success', 'counts': counts})
    return {'status': 'partial' if failed else 'available', 'jobs': jobs,
            'totals': totals, 'by_label': list(by_label.values()),
            'note': 'Đếm bản ghi API theo job, không nội suy track. Không phải số frame hoàn thành hoặc số đối tượng duy nhất toàn task.'}


def normalize(manifest, cvat, github, links, snapshot, session=None):
    task = (cvat or {}).get('task', {})
    jobs = (cvat or {}).get('jobs', [])
    host = manifest.get('scope', {}).get('cvat_host', 'https://app.cvat.ai').rstrip('/')
    warnings = []
    annotations = annotation_summary(cvat)
    if annotations['status'] != 'available':
        warnings.append('Annotations chưa đầy đủ; xem annotations.status và từng job trước khi sử dụng thống kê.')
    for source in ('cvat', 'github'):
        if manifest.get('sources', {}).get(source, {}).get('status') != 'success':
            warnings.append(f'Nguồn {source} chưa lấy thành công; dữ liệu mục liên quan chưa đầy đủ.')
    refs = {row['github_issue']: row for row in links}
    edges, questions, excluded = [], [], []
    for issue in (github or {}).get('issues', []):
        if 'pull_request' in issue:
            continue
        labels = [label['name'] for label in issue.get('labels', [])]
        if issue.get('title', '').lower().startswith('[api test]') or 'api-test' in labels:
            excluded.append({'number': issue['number'], 'reason': 'api_test'})
            continue
        if issue.get('state') != 'open':
            continue
        ref = refs.get(issue['number'], {})
        selected_task = manifest.get('scope', {}).get('task_id') or task.get('id')
        if selected_task is not None and ref.get('cvat_task_id') is not None and ref['cvat_task_id'] != selected_task:
            excluded.append({'number': issue['number'], 'reason': 'other_task',
                             'task_id': ref['cvat_task_id']})
            continue
        verified = ref.get('status') == 'verified'
        url = (f"{host}/tasks/{ref['cvat_task_id']}/jobs/{ref['cvat_job_id']}"
               if verified else None)
        item = {'number': issue['number'], 'title': issue.get('title'),
                'description': issue.get('body') or '', 'labels': labels,
                'source_url': issue.get('html_url'), 'state': issue.get('state'),
                'author': (issue.get('user') or {}).get('login'),
                'updated_at': issue.get('updated_at'),
                'task_id': ref.get('cvat_task_id'), 'job_id': ref.get('cvat_job_id'),
                'link_status': ref.get('status', 'unlinked'), 'cvat_job_url': url,
                'frame': None}
        if 'ca-kho' in labels:
            edges.append(item)
            if not verified:
                warnings.append(f"Ca khó #{issue['number']} chưa có liên kết CVAT được xác minh.")
        if 'mentor-question' in labels:
            questions.append(item)
            if not verified:
                warnings.append(f"Câu hỏi #{issue['number']} chưa có tham chiếu task/job được xác minh; có thể là câu hỏi chung của repo.")
    normalized_jobs = [{'job_id': job['id'], 'type': job.get('type'),
                        'stage': job.get('stage'), 'state': job.get('state'),
                        'assignee': (job.get('assignee') or {}).get('username'),
                        'frame_count': job.get('frame_count'),
                        'source_url': f"{host}/tasks/{job.get('task_id', task.get('id'))}/jobs/{job['id']}"}
                       for job in jobs]
    annotation_jobs = [job for job in jobs if job.get('type') == 'annotation']
    completed_jobs = sum(job.get('state') == 'completed' for job in annotation_jobs)
    return {'schema_version': 1,
            'metadata': {'snapshot': str(snapshot), 'snapshot_started_at': manifest.get('started_at'),
                         'snapshot_finished_at': manifest.get('finished_at'),
                         'generated_at': datetime.now(timezone.utc).isoformat(),
                         'mentor_session': session, 'scope': manifest.get('scope'),
                         'warnings': warnings, 'excluded_issues': excluded},
            'batch_progress': {'status': 'available' if cvat is not None else 'unavailable',
                               'task_id': task.get('id'), 'task_name': task.get('name'),
                               'total_frames': task.get('size'), 'jobs': normalized_jobs,
                               'jobs_by_stage': dict(Counter(j.get('stage') or 'unknown' for j in jobs)),
                               'jobs_by_state': dict(Counter(j.get('state') or 'unknown' for j in jobs)),
                               'annotation_job_count': len(annotation_jobs),
                               'completed_annotation_job_count': completed_jobs,
                               'completed_annotation_job_percent': (round(completed_jobs * 100 / len(annotation_jobs), 2)
                                                                    if annotation_jobs else None),
                               'completed_frames': None, 'completion_percent': None,
                               'note': 'Chưa suy ra tiến độ frame hoặc nghiệm thu từ trạng thái job.'},
            'scores': {'status': 'unavailable', 'value': None, 'method': None,
                       'source_url': None, 'scored_at': None,
                       'reason': 'Chưa thống nhất nguồn điểm và quy tắc chấm QA/QC.'},
            'annotations': annotations,
            'edge_cases': {'status': 'available' if github is not None else 'unavailable', 'items': edges},
            'open_questions': {'status': 'available' if github is not None else 'unavailable', 'items': questions}}


def cell(value):
    return str(value if value is not None else 'Chưa có').replace('|', '\\|').replace('\n', ' ').replace('\r', '')


def local_time(value):
    if not value:
        return 'Chưa có'
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(
        timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M:%S (UTC+7)')


def render(data):
    meta, progress = data['metadata'], data['batch_progress']
    lines = ['# Bản nháp báo cáo trước phiên mentor', '',
             f"Phiên mentor: {cell(meta['mentor_session'] or 'Chưa đặt tên phiên')}", '',
             f"Dữ liệu lấy lúc: {local_time(meta['snapshot_started_at'])}", '',
             f"Bản nháp tạo lúc: {local_time(meta['generated_at'])}", '',
             f"Snapshot nguồn: `{meta['snapshot']}`", '',
             'Bản nháp cần nhóm trưởng rà soát trước khi nộp. Task hiện được trình bày làm đơn vị batch.', '']
    if meta['warnings']:
        lines += ['Thông tin còn thiếu:', ''] + [f'- {w}' for w in meta['warnings']] + ['']
    lines += ['## 1. Tiến độ batch', '',
              f"Task: **{cell(progress['task_name'])}** — ID `{cell(progress['task_id'])}`; tổng frame: **{cell(progress['total_frames'])}**.", '',
              (f"Job gán nhãn có state `completed`: **{progress['completed_annotation_job_count']}/{progress['annotation_job_count']}**; tỷ lệ theo số job: **{str(progress['completed_annotation_job_percent']) + '%' if progress['completed_annotation_job_percent'] is not None else 'Chưa xác định'}**. Đây không phải tỷ lệ frame hoàn thành hoặc tỷ lệ QA duyệt."
               if progress['status'] == 'available' else 'Chưa lấy được dữ liệu CVAT; không có số liệu tiến độ đáng tin cậy.'), '',
              '| Job | Loại | Giai đoạn | Trạng thái | Người phụ trách | Số frame của job |',
              '|---|---|---|---|---|---|']
    for job in progress['jobs']:
        lines.append(f"| [{job['job_id']}]({job['source_url']}) | {cell(job['type'])} | {cell(job['stage'])} | {cell(job['state'])} | {cell(job['assignee'])} | {cell(job['frame_count'])} |")
    if not progress['jobs']:
        lines += ['', 'Chưa có dữ liệu jobs để trình bày.']
    lines += ['', progress['note'], '']
    annotations = data['annotations']
    if annotations['status'] in ('available', 'partial'):
        totals = annotations['totals']
        lines += [f"Annotations ({annotations['status']}): **{totals['shapes']} shapes**, **{totals['tracks']} tracks**, **{totals['tags']} tags**; **{totals['track_shape_records']} bản ghi shape trong tracks**.", '',
                  annotations['note'], '', '| Nhãn | Shapes | Tracks | Tags |', '|---|---|---|---|']
        for label in annotations['by_label']:
            lines.append(f"| {cell(label['label_name'])} (ID {cell(label['label_id'])}) | {label['shapes']} | {label['tracks']} | {label['tags']} |")
        lines += ['']
    else:
        lines += ['Chưa có annotations trong snapshot để thống kê.', '']
    lines += ['## 2. Điểm chấm', '', data['scores']['reason'],
              'Điểm hiện để trống; không coi thiếu dữ liệu là điểm 0.', '']
    for section, title in [('edge_cases', '3. Ca khó kèm link job'),
                           ('open_questions', '4. Câu hỏi mở')]:
        block = data[section]
        lines += [f'## {title}', '']
        if block['status'] == 'unavailable':
            lines += ['Chưa lấy được dữ liệu GitHub cho mục này.', '']
        elif not block['items']:
            label = 'ca-kho' if section == 'edge_cases' else 'mentor-question'
            lines += [f'Chưa có issue mở được gắn nhãn `{label}` trong snapshot (đã loại issue thử API).', '']
        for item in block['items']:
            lines += [f"### #{item['number']} — {cell(item['title'])}", '',
                      f"[Xem issue và nội dung đầy đủ]({item['source_url']})", '']
            # Quote source text to distinguish it from generated report statements.
            lines += ['> ' + line for line in (item['description'] or 'Chưa có mô tả.').splitlines()] + ['']
            if item['cvat_job_url']:
                lines += [f"[Mở job CVAT]({item['cvat_job_url']}) — đã xác minh quan hệ task/job; chưa xác minh frame.", '']
            else:
                lines += [f"Liên kết CVAT: chưa xác minh ({item['link_status']}).", '']
    return '\n'.join(lines) + '\n'


def generate(snapshot, session=None):
    manifest = json.loads((snapshot / 'manifest.json').read_text(encoding='utf-8'))
    def source(name):
        if manifest.get('sources', {}).get(name, {}).get('status') != 'success':
            return None
        return json.loads((snapshot / f'{name}.json').read_text(encoding='utf-8'))
    links = json.loads((snapshot / 'links.json').read_text(encoding='utf-8')) if (snapshot / 'links.json').exists() else []
    data = normalize(manifest, source('cvat'), source('github'), links, snapshot, session)
    write_json(snapshot / 'report_data.json', data)
    (snapshot / 'MENTOR_REPORT_DRAFT.md').write_text(render(data), encoding='utf-8')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--session', help='Tên phiên mentor hoặc kỳ báo cáo')
    args = parser.parse_args()
    generate(args.snapshot, args.session)
    print('Report:', args.snapshot / 'MENTOR_REPORT_DRAFT.md')


if __name__ == '__main__':
    main()
