import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('collect', Path(__file__).parents[1] / 'src/collect.py')
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


def response(payload, links=None):
    result = Mock(status_code=200, links=links or {})
    result.json.return_value = payload
    return result


class CollectorTests(unittest.TestCase):
    def test_cvat_collects_all_pages(self):
        client = collect.Client('https://app.cvat.ai', 'test')
        client.get = Mock(side_effect=[
            response({'results': [{'id': 1}], 'next': 'https://app.cvat.ai/api/jobs?page=2'}),
            response({'results': [{'id': 2}], 'next': None})])
        self.assertEqual(client.listing('api/jobs', {'task_id': 9}), [{'id': 1}, {'id': 2}])

    def test_github_follows_link_and_excludes_pr(self):
        client = collect.Client('https://api.github.com', 'test')
        client.get = Mock(side_effect=[
            response([{'number': 1}], {'next': {'url': 'https://api.github.com/repos/a/b/issues?page=2'}}),
            response([{'number': 2, 'pull_request': {}}]), response([]), response([])])
        payload = collect.github_snapshot(client, 'a/b')
        self.assertEqual(payload['issues'], [{'number': 1}])
        self.assertEqual(client.get.call_count, 4)

    def test_failed_request_is_not_empty_success(self):
        client = collect.Client('https://app.cvat.ai', 'test')
        client.session.get = Mock(return_value=Mock(status_code=403))
        with self.assertRaisesRegex(RuntimeError, '403'):
            client.listing('api/issues')

    def test_pagination_cannot_send_token_to_other_host(self):
        client = collect.Client('https://app.cvat.ai', 'test')
        client.session.get = Mock()
        with self.assertRaises(ValueError):
            client.get('https://example.com/api/jobs')
        client.session.get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
