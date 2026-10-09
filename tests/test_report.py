import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from report import normalize, render


class ReportTests(unittest.TestCase):
    def test_other_task_issue_excluded_but_general_question_kept(self):
        issues = [{'number': n, 'title': 'Question', 'state': 'open',
                   'labels': [{'name': 'mentor-question'}]} for n in (1, 2)]
        data = normalize({'scope': {'task_id': 10}, 'sources': {}}, None,
                         {'issues': issues}, [{'github_issue': 1, 'cvat_task_id': 20,
                                               'cvat_job_id': 30, 'status': 'verified'}], Path('sample'))
        self.assertEqual([i['number'] for i in data['open_questions']['items']], [2])
        self.assertEqual(data['metadata']['excluded_issues'][0]['reason'], 'other_task')

    def test_job_progress_excludes_ground_truth(self):
        cvat = {'task': {'id': 1}, 'jobs': [
            {'id': 1, 'type': 'annotation', 'state': 'completed'},
            {'id': 2, 'type': 'annotation', 'state': 'in progress'},
            {'id': 3, 'type': 'ground_truth', 'state': 'completed'}]}
        data = normalize({'sources': {}}, cvat, None, [], Path('sample'))
        self.assertEqual(data['batch_progress']['completed_annotation_job_percent'], 50)
        self.assertEqual(data['batch_progress']['annotation_job_count'], 2)

    def test_test_issue_excluded_and_missing_score_not_zero(self):
        manifest = {'sources': {'cvat': {'status': 'success'}, 'github': {'status': 'success'}}}
        github = {'issues': [{'number': 1, 'title': '[API test] demo', 'state': 'open',
                             'labels': [{'name': 'ca-kho'}]}]}
        data = normalize(manifest, {'task': {'id': 1, 'size': 190}, 'jobs': []}, github, [], Path('sample'))
        self.assertEqual(data['edge_cases']['items'], [])
        self.assertIsNone(data['scores']['value'])
        self.assertIsNone(data['batch_progress']['completion_percent'])

    def test_failed_source_is_not_no_issues(self):
        data = normalize({'sources': {}}, None, None, [], Path('sample'))
        self.assertEqual(data['edge_cases']['status'], 'unavailable')
        self.assertIn('Chưa lấy được dữ liệu GitHub', render(data))

    def test_unverified_issue_remains_visible_without_job_link(self):
        github = {'issues': [{'number': 2, 'title': 'Real case', 'state': 'open',
                  'labels': [{'name': 'ca-kho'}, {'name': 'mentor-question'}],
                  'body': 'Question', 'html_url': 'https://github.com/a/b/issues/2'}]}
        data = normalize({'sources': {'github': {'status': 'success'}}}, None, github,
                         [{'github_issue': 2, 'status': 'mismatch'}], Path('sample'))
        self.assertEqual(len(data['open_questions']['items']), 1)
        self.assertIsNone(data['edge_cases']['items'][0]['cvat_job_url'])
