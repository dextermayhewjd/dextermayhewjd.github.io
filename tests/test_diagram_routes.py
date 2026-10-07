"""Keep the wide overviews readable: no shared line runs or paths through nodes."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def segments(d):
    tokens = re.findall(r'[MHVL]|-?\d+(?:\.\d+)?', d)
    x = y = 0
    result = []
    i = 0
    while i < len(tokens):
        command = tokens[i]; i += 1
        if command in ('M', 'L'):
            nx, ny = map(float, tokens[i:i+2]); i += 2
        elif command == 'H':
            nx, ny = float(tokens[i]), y; i += 1
        elif command == 'V':
            nx, ny = x, float(tokens[i]); i += 1
        else:
            raise ValueError(d)
        if command != 'M' and (x, y) != (nx, ny):
            result.append((x, y, nx, ny))
        x, y = nx, ny
    return result

class OverviewRoutes(unittest.TestCase):
    def test_wide_routes(self):
        for chapter, filename in [('s08', 'compact-agent-integration.svg'),
                                  ('s09', 'memory-agent-integration.svg'),
                                  ('s10', 'task-agent-integration.svg'),
                                  ('s10', 'task-core.svg'),
                                  ('s11', 'background-agent-integration.svg'),
                                  ('s11', 'background-core.svg'),
                                  ('s12', 'cron-agent-integration.svg'),
                                  ('s12', 'cron-core.svg'),
                                  ('s13', 'team-agent-integration.svg'),
                                  ('s13', 'team-core.svg'),
                                  ('s13', 'team-messaging.svg'),
                                  ('s13', 'team-protocol.svg'),
                                  ('s13', 'team-claiming.svg'),
                                  ('s13', 'team-worktree.svg'),
                                  ('s14', 'mcp-agent-integration.svg'),
                                  ('s14', 'mcp-core.svg'),
                                  ('s14', 'mcp-tool-search-extension.svg'),
                                  ('s15', 'harness-agent-integration.svg'),
                                  ('s15', 'harness-core.svg'),
                                  ('s15/system-prompt', 'system-prompt-flow.svg'),
                                  ('s15/system-prompt', 'skills-context-flow.svg'),
                                  ('s16', 'workflow-agent-integration.svg'),
                                  ('s16', 'workflow-core.svg'),
                                  ('s17', 'goal-agent-integration.svg'),
                                  ('s17', 'goal-core.svg')]:
            with self.subTest(chapter=chapter, diagram=filename):
                root = ET.parse(ROOT/'content/projects/learn-claude-code'/chapter/'images'/filename).getroot()
                expected_width = 760 if chapter.endswith('/system-prompt') else 1200 if filename.endswith('agent-integration.svg') else 1000
                self.assertEqual(float(root.get('viewBox').split()[2]), expected_width)
                for node in root.iter():
                    if node.get('data-stage'):
                        self.assertLessEqual(float(node.get('stroke-width')), 2, 'Widening must not scale borders')
                nodes = [(n.get('data-stage'), *[float(n.get(a)) for a in ('x', 'y', 'width', 'height')])
                         for n in root.iter() if n.tag.split('}')[-1] == 'rect' and n.get('data-stage')]
                stages = {node[0] for node in nodes}
                for edge in root.iter():
                    if not edge.get('data-route'):
                        continue
                    self.assertIn(edge.get('data-from'), stages, 'Missing or stale source endpoint')
                    self.assertIn(edge.get('data-to'), stages, 'Missing or stale destination endpoint')
                    self.assertIn(edge.get('data-kind'), ('flow', 'reference'))
                    self.assertTrue(edge.get('data-label'), 'The arrow needs a readable meaning')
                lines = [(n.get('data-route'), segments(n.get('d')))
                         for n in root.iter() if n.tag.split('}')[-1] == 'path' and n.get('stroke')]
                for name, runs in lines:
                    for x, y, xx, yy in runs:
                        for node, left, top, width, height in nodes:
                            horizontal = y == yy and top < y < top+height and max(min(x, xx), left) < min(max(x, xx), left+width)
                            vertical = x == xx and left < x < left+width and max(min(y, yy), top) < min(max(y, yy), top+height)
                            self.assertFalse(horizontal or vertical, f'{chapter}: {name} crosses {node}')
                for i, (name, runs) in enumerate(lines):
                    for other, other_runs in lines[i+1:]:
                        for x,y,xx,yy in runs:
                            for a,b,aa,bb in other_runs:
                                horizontal = y == yy == b == bb and max(min(x,xx),min(a,aa)) < min(max(x,xx),max(a,aa))
                                vertical = x == xx == a == aa and max(min(y,yy),min(b,bb)) < min(max(y,yy),max(b,bb))
                                self.assertFalse(horizontal or vertical, f'{chapter}: {name} overlaps {other}')

if __name__ == '__main__':
    unittest.main()
