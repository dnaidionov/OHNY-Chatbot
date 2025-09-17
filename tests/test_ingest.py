import json
import subprocess
import os
import tempfile


def test_ingest_generates_synthetic_json(tmp_path):
    # Run ingest.py in the backend folder and write output into tmp_path
    backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
    backend_dir = os.path.abspath(backend_dir)
    out_file = tmp_path / 'synthetic_events.json'

    # Run the script with --synthetic and a small count
    cmd = ['python3', os.path.join(backend_dir, 'ingest.py'), '--synthetic', '--count', '5']
    # Ensure we run with cwd set to tmp_path so files are written there
    subprocess.check_call(cmd, cwd=tmp_path)

    assert out_file.exists(), 'synthetic_events.json was not created'

    data = json.loads(out_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 5
