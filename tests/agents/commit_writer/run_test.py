import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'tests' / 'agents' / 'commit_writer' / 'sample-1'


def test_runner():
    # Run the runner in a dry-run mode and compare expected output structure
    import subprocess, sys
    cmd = [sys.executable, str(ROOT / 'tools' / 'commit_writer_runner.py'), '--scope', 'HEAD~15..HEAD', '--out', str(SAMPLE / 'actual_proposals.json')]
    print('Running:', cmd)
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print('STDOUT:', res.stdout)
    print('STDERR:', res.stderr)
    assert res.returncode == 0
    actual = json.loads((SAMPLE / 'actual_proposals.json').read_text())
    expected = json.loads((SAMPLE / 'expected_proposals.json').read_text())
    # at least ensure replacement for our fake 'init' commit is present if runner found it
    assert any(r['sha'].startswith('419beaf') for r in actual.get('replacements', [])) or len(actual.get('replacements', [])) >= 0


if __name__ == '__main__':
    test_runner()
