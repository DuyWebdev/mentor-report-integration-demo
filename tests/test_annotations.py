import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from report import annotation_summary


class AnnotationTests(unittest.TestCase):
    def test_shapes_only_supported(self):
        result = annotation_summary({'labels': [{'id': 1, 'name': 'vehicle'}],
            'annotations': [{'job_id': 4, 'status': 'success', 'data': {
                'shapes': [{'label_id': 1, 'frame': 0}, {'label_id': 1, 'frame': 0}],
                'tracks': [], 'tags': []}}]})
        self.assertEqual(result['totals'], {'shapes': 2, 'tracks': 0,
                                          'tags': 0, 'track_shape_records': 0})

    def test_tracks_not_expanded_to_frame_completion(self):
        result = annotation_summary({'labels': [{'id': 1, 'name': 'vehicle'}],
            'annotations': [{'job_id': 3, 'status': 'success', 'data': {
                'tracks': [{'label_id': 1, 'shapes': [{'frame': 0}, {'frame': 170}]}],
                'shapes': [{'label_id': 1}], 'tags': []}}]})
        self.assertEqual(result['totals']['tracks'], 1)
        self.assertEqual(result['totals']['track_shape_records'], 2)
        self.assertEqual(result['by_label'][0]['label_name'], 'vehicle')

    def test_failed_job_not_zero_success(self):
        result = annotation_summary({'annotations': [{'job_id': 3, 'status': 'failed'}]})
        self.assertEqual(result['status'], 'partial')
        self.assertIsNone(result['jobs'][0]['counts'])

    def test_old_snapshot_supported(self):
        self.assertEqual(annotation_summary({'jobs': []})['status'], 'unavailable')
