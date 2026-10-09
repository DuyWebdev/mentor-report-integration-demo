import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from sync import link_issues


class SyncTests(unittest.TestCase):
    def test_links_preserve_unlinked_invalid_and_mismatch(self):
        client = Mock()
        issues = [{'number': n, 'html_url': 'example', 'body': body}
                  for n, body in enumerate(['General question', 'CVAT task ID: 1',
                    'CVAT task ID: 1\nCVAT job ID: 3',
                    'CVAT task ID: 2\nCVAT job ID: 3'], 1)]
        rows = link_issues(issues, client, [{'id': 3, 'task_id': 1}])
        self.assertEqual([r['status'] for r in rows],
                         ['unlinked', 'invalid_reference', 'verified', 'mismatch'])
        client.get.assert_not_called()

    def test_inaccessible_job_is_not_mismatch(self):
        client = Mock()
        client.get.side_effect = RuntimeError('HTTP 403')
        rows = link_issues([{'number': 1, 'html_url': 'example',
                            'body': 'CVAT task ID: 1\nCVAT job ID: 3'}], client, [])
        self.assertEqual(rows[0]['status'], 'verification_failed')
