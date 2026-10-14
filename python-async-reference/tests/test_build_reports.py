import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / 'tools/build_reports.py'


def load_module():
    spec = importlib.util.spec_from_file_location('async_reference_reports', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def document(identifier, names):
    return {
        'id': identifier, 'url': f'https://docs.python.org/3.16/library/{identifier}.html',
        'title': identifier, 'category': 'asyncio', 'status': 'ok',
        'symbols': [{'name': n, 'url': f'https://docs.python.org/3.16/library/{identifier}.html#{n}',
                     'kind': 'method', 'signature': n} for n in names],
    }


def event(identifier, name, kind='api_call', resolution='direct', scope='core'):
    return {'id': identifier, 'canonical_name': name, 'kind': kind,
            'resolution': resolution, 'scope': scope, 'name': name or 'get',
            'file': 'slime/demo.py', 'line': 7}


class ReportModels(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_document_aliases_match_without_double_counting(self):
        docs = [document('asyncio-eventloop', ['loop.create_task', 'asyncio.AbstractEventLoop.create_task']),
                document('asyncio-task', ['asyncio.Task.cancel', 'asyncio.TaskGroup'])]
        inventories = {'slime': {'source': {}, 'occurrences': [
            event('1', 'asyncio.AbstractEventLoop.create_task'),
            event('2', 'asyncio.Task.cancel', 'inferred_method', 'inferred'),
        ]}}
        report = self.module.build_report_data({'documents': docs}, inventories)
        by_name = {a['name']: a for a in report['apis']}
        self.assertEqual(by_name['asyncio.AbstractEventLoop.create_task']['counts']['slime']['direct_calls'], 1)
        self.assertEqual(by_name['asyncio.Task.cancel']['counts']['slime']['direct_calls'], 0)
        self.assertEqual(by_name['asyncio.Task.cancel']['counts']['slime']['inferred_calls'], 1)
        self.assertEqual(by_name['asyncio.TaskGroup']['counts']['slime']['direct_calls'], 0)
        page = next(d for d in report['documents'] if d['id'] == 'asyncio-eventloop')
        self.assertEqual(page['counts']['slime']['direct_calls'], 1)

    def test_unknown_method_is_not_attributed_from_its_name(self):
        docs = [document('asyncio-queue', ['asyncio.Queue.get'])]
        report = self.module.build_report_data({'documents': docs}, {
            'slime': {'source': {}, 'occurrences': [event('1', None, 'instance_candidate', 'unresolved')]}
        })
        self.assertEqual(report['apis'][0]['counts']['slime']['direct_calls'], 0)
        self.assertEqual(report['apis'][0]['counts']['slime']['inferred_calls'], 0)
        self.assertEqual(len(report['candidates']), 1)

    def test_references_and_test_calls_do_not_become_core_calls(self):
        report = self.module.build_report_data({'documents': [document('asyncio-task', ['asyncio.Task'])]}, {
            'slime': {'source': {}, 'occurrences': [
                event('1', 'asyncio.Task', 'api_reference'),
                event('2', 'asyncio.Task', scope='tests'),
            ]}
        })
        counts = report['apis'][0]['counts']['slime']
        self.assertEqual(counts['references'], 1)
        self.assertEqual(counts['direct_calls'], 1)
        self.assertEqual(counts['core_direct_calls'], 0)

    def test_broader_reference_filters_unrelated_apis(self):
        docs = [document('inspect', ['inspect.signature', 'inspect.isawaitable'])]
        docs[0]['category'] = 'stdlib'
        report = self.module.build_report_data({'documents': docs}, {})
        self.assertEqual([a['name'] for a in report['apis']], ['inspect.isawaitable'])

    def test_language_and_os_pages_only_include_async_and_process_interfaces(self):
        docs = [document('reference-datamodel', ['object.__await__', 'object.__add__', 'function.__name__']),
                document('os', ['os.getpid', 'os.execvp', 'os.listdir', 'os.getenv']),
                document('fcntl', ['fcntl.flock', 'fcntl.ioctl'])]
        docs[0]['url'] = 'https://docs.python.org/3.16/reference/datamodel.html'
        report = self.module.build_report_data({'documents': docs}, {})
        self.assertEqual({a['name'] for a in report['apis']},
                         {'object.__await__', 'os.getpid', 'os.execvp', 'fcntl.flock'})

    def test_unmatched_native_api_is_preserved(self):
        report = self.module.build_report_data({'documents': []}, {
            'slime': {'source': {}, 'occurrences': [event('1', 'asyncio.some_future_api')]}
        })
        self.assertEqual(report['unmapped'][0]['canonical_name'], 'asyncio.some_future_api')

    def test_factory_and_inherited_methods_match_documented_class(self):
        docs = [document('multiprocessing', ['multiprocessing.pool.Pool', 'multiprocessing.pool.Pool.starmap']),
                document('threading', ['threading.Thread.start'])]
        report = self.module.build_report_data({'documents': docs}, {
            'slime': {'source': {}, 'occurrences': [
                event('1', 'multiprocessing.context.BaseContext.Pool', 'inferred_method', 'inferred'),
                event('2', 'multiprocessing.Pool.starmap', 'inferred_method', 'inferred'),
                event('3', 'threading.Timer.start', 'inferred_method', 'inferred'),
            ]}
        })
        self.assertEqual(report['unmapped'], [])
        by_name = {a['name']: a for a in report['apis']}
        for name in ('multiprocessing.pool.Pool', 'multiprocessing.pool.Pool.starmap', 'threading.Thread.start'):
            self.assertEqual(by_name[name]['counts']['slime']['inferred_calls'], 1)

    def test_report_refresh_removes_only_previously_managed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'personal-notes.md').write_text('keep')
            self.module.write_outputs(root, {'old-topic.md': 'old'})
            self.assertIn('old-topic.md', self.module.write_outputs(root, {'new-topic.md': 'new'}, check=True))
            self.assertTrue((root / 'old-topic.md').exists())
            self.module.write_outputs(root, {'new-topic.md': 'new'})
            self.assertFalse((root / 'old-topic.md').exists())
            self.assertEqual((root / 'personal-notes.md').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
