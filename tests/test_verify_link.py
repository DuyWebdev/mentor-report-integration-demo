import sys
from pathlib import Path
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from verify_link import extract_ids, verify


class LinkTests(unittest.TestCase):
    def test_crlf_body(self):
        self.assertEqual(extract_ids('CVAT task ID: 2592622\r\nCVAT job ID: 4475446\r\n'),
                         (2592622, 4475446))

    def test_ambiguous_ids_rejected(self):
        with self.assertRaises(ValueError):
            extract_ids('CVAT task ID: 1\nCVAT task ID: 2\nCVAT job ID: 3')

    def test_mismatch_is_not_verified(self):
        github, cvat = Mock(), Mock()
        github.get.return_value.json.return_value = {
            'number': 1, 'html_url': 'https://github.com/a/b/issues/1',
            'body': 'CVAT task ID: 1\nCVAT job ID: 3'}
        cvat.get.return_value.json.return_value = {'id': 3, 'task_id': 2}
        self.assertFalse(verify(github, cvat, 'a/b', 1)['relationship_verified'])


if __name__ == '__main__':
    unittest.main()
