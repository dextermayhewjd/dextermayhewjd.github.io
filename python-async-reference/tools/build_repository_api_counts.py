#!/usr/bin/env python3
"""Add a repository's API counts without rewriting the three-repository baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from build_reports import build_report_data
from api_usage_data import add_inherited_apis

ROOT = Path(__file__).resolve().parents[1]


def build_counts(repo):
    inventory_path = ROOT / 'repositories' / repo / 'inventory.json'
    raw = inventory_path.read_bytes()
    inventory = json.loads(raw)
    catalog = json.loads((ROOT / 'official/catalog.json').read_text())
    report = build_report_data(catalog, {repo: inventory})
    registry = {api['name']: api for api in report['apis']}
    add_inherited_apis(registry, {repo: inventory})
    scope = json.loads((ROOT / 'current-api-plan.json').read_text())
    selected = {name for group in scope['api_groups'] for name in group['apis']}
    core = {event['id'] for event in inventory['occurrences']
            if event['scope'] == 'core' and event['kind'] in ('api_call', 'inferred_method')}
    covered = {identifier for api in registry.values() if api['name'] in selected
               for identifier in api['occurrences'][repo] if identifier in core}
    return {
        'schema_version': 1,
        'repository': repo,
        'source_head': inventory['source']['head'],
        'source_root': inventory['source']['root'],
        'inventory_sha256': hashlib.sha256(raw).hexdigest(),
        'counting_policy': report['counting_policy'],
        'apis': [{'name': api['name'], 'counts': api['counts'][repo],
                  'occurrences': api['occurrences'][repo]} for api in sorted(registry.values(), key=lambda item: item['name'])],
        'unmapped_occurrences': [event['id'] for event in report['unmapped']
                                if event['canonical_name'] not in registry],
        'unresolved_candidate_count': len(report['candidates']),
        'curriculum_coverage': {
            'selected_api_count': len(selected),
            'covered_core_call_positions': len(covered),
            'all_core_call_positions': len(core),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', args.repo):
        parser.error('--repo must be a safe lowercase repository name')
    content = json.dumps(build_counts(args.repo), ensure_ascii=False, indent=2) + '\n'
    destination = ROOT / 'repositories' / args.repo / 'api-counts.json'
    if args.check:
        if not destination.exists() or destination.read_text() != content:
            raise SystemExit(f'Stale {destination}; regenerate repository API counts')
    else:
        destination.write_text(content)
    print(f'{args.repo} API counts {"verified" if args.check else "written"}.')


if __name__ == '__main__':
    main()
