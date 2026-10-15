"""Read the four frozen inventories without rewriting the original report."""
import hashlib
import json
from pathlib import Path

from build_reports import add_count, blank_counts

ROOT = Path(__file__).resolve().parents[1]
REPOS = ('verl', 'areal', 'slime', 'miles')
LABELS = {'verl': 'verl', 'areal': 'AReaL', 'slime': 'Slime', 'miles': 'Miles'}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def add_inherited_apis(registry, inventories):
    # pop_all is documented on ExitStack and inherited by AsyncExitStack.
    # The frozen report's selective contextlib catalog omitted that entry.
    name = 'contextlib.AsyncExitStack.pop_all'
    entry = {
        'name': name,
        'docs': [{'url': 'https://docs.python.org/3.16/library/contextlib.html#contextlib.ExitStack.pop_all'}],
        'counts': {}, 'occurrences': {},
    }
    for repo, inventory in inventories.items():
        entry['counts'][repo] = blank_counts()
        entry['occurrences'][repo] = []
        for event in inventory['occurrences']:
            if (event.get('canonical_name') == name
                    and event['kind'] in ('api_call', 'inferred_method', 'api_reference')
                    and event.get('resolution') != 'unresolved'):
                add_count(entry['counts'][repo], event)
                entry['occurrences'][repo].append(event['id'])
    registry[name] = entry


def load_usage():
    registry = {item['name']: item for item in read_json(ROOT / 'report.json')['apis']}
    inventories = {repo: read_json(ROOT / 'repositories' / repo / 'inventory.json') for repo in REPOS}
    add_inherited_apis(registry, inventories)
    for repo in REPOS:
        if repo in next(iter(registry.values()))['counts']:
            continue
        additional = read_json(ROOT / 'repositories' / repo / 'api-counts.json')
        inventory_path = ROOT / 'repositories' / repo / 'inventory.json'
        if additional['inventory_sha256'] != hashlib.sha256(inventory_path.read_bytes()).hexdigest():
            raise ValueError(f'{repo}: regenerate repository API counts after updating its inventory')
        extra = {item['name']: item for item in additional['apis']}
        if extra.keys() != registry.keys():
            raise ValueError(f'{repo}: API registry changed; regenerate repository API counts')
        for name, item in registry.items():
            item['counts'][repo] = extra[name]['counts']
            item['occurrences'][repo] = extra[name]['occurrences']
    return registry, inventories


def call_statistics(registry, inventories, selected):
    result = {}
    for repo, inventory in inventories.items():
        core = {event['id']: event for event in inventory['occurrences']
                if event['scope'] == 'core' and event['kind'] in ('api_call', 'inferred_method')}
        covered = {identifier for name in selected for identifier in registry[name]['occurrences'][repo]
                   if identifier in core}
        result[repo] = {'core': core, 'covered': covered}
    return result
