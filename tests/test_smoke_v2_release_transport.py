"""Offline contract tests for V2 GitHub Release transport (no network calls)."""

import gzip
import hashlib
import json
import os
import subprocess
import textwrap
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "e001_v2_release_raw.sh"
WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "e001-24h-verification-v2.yml"
)
SHA = "a" * 40


def fake_gh(tmp_path: Path) -> tuple[dict[str, str], Path]:
    commands = tmp_path / "bin"
    commands.mkdir()
    store = tmp_path / "fake-releases"
    store.mkdir()
    gh = commands / "gh"
    gh.write_text(textwrap.dedent("""\
        #!/usr/bin/env python3
        import fnmatch
        import os
        import pathlib
        import shutil
        import sys

        args = sys.argv[1:]
        assert args.pop(0) == "release"
        command = args.pop(0)
        store = pathlib.Path(os.environ["FAKE_RELEASE_STORE"])
        if command == "create":
            tag = args[0]
            if (store / tag).exists():
                sys.exit("duplicate release")
            (store / tag).mkdir()
        elif command == "upload":
            tag = args.pop(0)
            destination = store / tag
            files = args[:args.index("--repo")]
            for filename in files:
                source = pathlib.Path(filename)
                target = destination / source.name
                if target.exists() or not source.is_file():
                    sys.exit("unsafe duplicate/missing asset")
                shutil.copyfile(source, target)
        elif command == "download":
            tag = args.pop(0)
            source = store / tag
            target = pathlib.Path(args[args.index("--dir") + 1])
            target.mkdir(parents=True, exist_ok=True)
            patterns = [args[i + 1] for i, item in enumerate(args[:-1]) if item == "--pattern"]
            matches = [p for p in source.iterdir()
                       if any(fnmatch.fnmatch(p.name, pattern) for pattern in patterns)]
            if not matches:
                sys.exit("missing release assets")
            for asset in matches:
                shutil.copyfile(asset, target / asset.name)
        else:
            sys.exit("unsupported fake gh command")
    """))
    gh.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{commands}:{os.environ['PATH']}",
        "FAKE_RELEASE_STORE": str(store),
        "GITHUB_REPOSITORY": "williammolina489/kalshi-market-maker-research",
        "GITHUB_SHA": SHA,
    }
    return env, store


def call(*args: str, env: dict[str, str], check: bool = True):
    return subprocess.run(["bash", str(SCRIPT), *map(str, args)], env=env,
                          text=True, capture_output=True, check=check)


def build_chunk(root: Path, number: int) -> str:
    root.mkdir(parents=True, exist_ok=True)
    segment = root / f"observations-chunk-{number}.jsonl.gz"
    with gzip.open(segment, "wt", encoding="utf8") as handle:
        handle.write('{"source":"public_test_only","number":' + str(number) + '}\n')
    digest = hashlib.sha256(segment.read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps({
        "segments": [{"path": segment.name, "sha256": digest}]
    }))
    for name in ("restart.json", "smoke_runtime.json", f"chunk-summary-{number}.json",
                 "verification-authorization.json"):
        (root / name).write_text('{"only":"public_offline_fixture"}')
    return digest


def test_release_upload_restore_and_full_raw_replay(tmp_path: Path) -> None:
    env, store = fake_gh(tmp_path)
    root = tmp_path / "capture"
    call("init", env=env)
    expected = {}
    for i in range(1, 6):
        expected[i] = build_chunk(root, i)
        call("upload", str(root), str(i), env=env)
    restore = tmp_path / "checkpoint"
    call("restore", str(restore), "5", env=env)
    assert json.loads((restore / "smoke_runtime.json").read_text()) == {
        "only": "public_offline_fixture"
    }
    full = tmp_path / "replay"
    call("download-all", str(full), env=env)
    for i in range(1, 6):
        segment = full / f"observations-chunk-{i}.jsonl.gz"
        assert hashlib.sha256(segment.read_bytes()).hexdigest() == expected[i]
    # Existing release assets cannot be silently replaced or cleared.
    assert call("upload", str(root), "5", env=env, check=False).returncode != 0
    assert (store / ("kalshi-e001-v2-" + SHA[:12])).exists()


def test_corrupt_release_checkpoint_fails_closed(tmp_path: Path) -> None:
    env, store = fake_gh(tmp_path)
    root = tmp_path / "capture"
    call("init", env=env)
    build_chunk(root, 1)
    call("upload", str(root), "1", env=env)
    asset = store / ("kalshi-e001-v2-" + SHA[:12]) / "e001-v2-state-1.tar.gz"
    asset.write_bytes(asset.read_bytes() + b"modified")
    assert call("restore", str(tmp_path / "restore"), "1", env=env, check=False).returncode != 0


def test_transport_and_workflow_use_no_actions_artifact_storage() -> None:
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
    text = WORKFLOW.read_text()
    assert "upload-artifact" not in text
    assert "download-artifact" not in text
    assert "actions/cache" not in text
    assert "e001_v2_release_raw.sh" in text
    assert "research/E001_VERIFICATION_V2_AUTHORIZATION.json" in text
