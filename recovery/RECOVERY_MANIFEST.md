# E001 Exact-Recovery Manifest

Recovery classification: **RECOVERY PARTIAL — MATERIAL FILES MISSING**

This document is recovery metadata only. It does not reconstruct source, change E001 methodology,
publish the collector, start a smoke, or start E001.

## Source-of-truth refs

- main: `7a189c27ca8cd5c9debeb079f4661ebd7b30c29c`
- research/e001-collector-smoke: `7a189c27ca8cd5c9debeb079f4661ebd7b30c29c`
- prior recovery commit: `7398fc455682d21980ea37ff8f542a5c0ce78f96`
- prior temporary object commit: `35e9558675fb3346574a731adc5e6669ff1ae6f0`
- original preserved bundle blob: `673f0cf8f1f432c2a5d720df1b62dd5a6a82c49a`
- tolerant recovery workflow run: `35479712486`
- exact dangling-object preservation run: `35479869552`

## Partial stream

- outer encoded bytes: 10,000
- compressed bytes: 7,500
- compressed SHA-256: `8fba70a92ccf61f225798f026ae9bf1d8e76ad1a9cf0b246284054e0e6289c48`
- gzip exit status: 1
- partial decompressed bytes: 29,281
- decompressed SHA-256: `4e025c31cf48e3efae2221f8f66cfc249b6b0a163fd05725b62128cc3f16279f`
- format: GNU/POSIX tar
- tar list exit status: 2
- tar --ignore-zeros list exit status: 2
- tar extraction exit status: 2
- end-of-archive two-zero-block marker: not present
- member headers observed: 10
- provably complete members: 9
- incomplete member: `SECURITY.md`
- SECURITY tar header size: 1,388 bytes
- SECURITY expected data end: byte 29,548
- stream end: byte 29,281
- GNU tar wrote only 1,024 bytes for the incomplete SECURITY member; that output is not accepted as a valid recovered file.

## Provably complete tar members

| Path | Bytes | SHA-256 | Git blob identity |
| --- | ---: | --- | --- |
| .github/workflows/ci.yml | 397 | `aa222d803a06a8a17178fdd8072005829b8a6eb2b37f5687fc112765a482a7ce` | `751eb467a909f75b70c7a44f47cec0f7283a62df` |
| .github/workflows/e001-smoke-bootstrap.yml | 3,823 | `c0bfd34957c9327763587d8a1722fc02f15cddab5b831eb1c8c1e379fd4045e1` | `efe2045600eca6360f65e253d48bf9a86101c986` |
| .github/workflows/e001-smoke-finalize.yml | 2,751 | `4185810830f4fd9b6e9717ea5a1d8b1252a9ed1da59f530891f119fb3a712fdd` | `eacaeb93469eefe57534268c4f5053e0d7cd2e1b` |
| .github/workflows/e001-smoke-segment.yml | 5,183 | `c0cad362c1408e8c4ac119ea37d3954e23fb158ae383850d54dae9cda170c273` | calculated `cefd0bbe8c68919ecc2572c9a656ae656aaa6b20`; this Git blob is not present via GitHub API |
| ARCHITECTURE.md | 2,480 | `080e77b80cd00764a6813e08b1cb276f165d1b4c826fb3246ee4253af2ba2673` | `e7c90b01fe5b13d7fca4f04de7c69c6529ac8180` |
| DATA_SOURCES.md | 1,931 | `964d1243e2664709510afc0aa539af2aef1828c36fe9985a0096e45cc07e360d` | `09bd20cb0aa71a8498a7b644a44015a8406b3b9a` |
| EXPERIMENTS.md | 836 | `ebe92ea704d0bd431d287114e8f8e9579437afc99ac36f6c8bf18bb095e79d5d` | `a27a65c63d5ec106c02831f7aa0d2e7e0986f9a1` |
| PROJECT_STATE.md | 2,204 | `0a922b897b79f10c20d5978851743e058bb84d480add00ea4b09ee55d24543b4` | `0badffb431d8aa433e1c47556e0fe5fee48862bc` |
| ROADMAP.md | 1,328 | `17e57e287a7467c8e3fd377d2b478592830268588b8eb903aa6511d5783fc8bd` | `fba2168bfad218937a375d3900381b76059d9b2d` |

## Additional exact dangling Git blobs preserved

All objects below were fetched by exact SHA and verified with `git hash-object`.

| Path / variant | Bytes | SHA-256 | Git blob |
| --- | ---: | --- | --- |
| .github/workflows/e001-smoke-segment.dangling-variant.yml | 5,183 | `59d66a5362b2409482ad9e7d6e68ecd3be186a9892843e015f182f019bb53a6f` | `241baa62e3d005a039aec57a7b14cc91f0430e18` |
| SECURITY.md | 1,388 | `aa7fe00a1011d0ecfaad81466bbdcbbfea6c6e5a6586264179714343a8769fd5` | `d502d6aeacfc4a9438593b695b7ab11b59d12a37` |
| docs/COLLECTOR_RUNBOOK.md | 2,607 | `cffcd86defb5aef3e8a06aba8faf94ece9075583424a632d2f2b22b8f613085b` | `23b5197848451a3db32c120bce9d6bdd0c99b637` |
| pyproject.toml | 582 | `8fea08454456a450f6ad73d25a7a2718a79db4baea8ff2b7c16beb48e5bf5206` | `7b17ce693cb1d31f192288a5c3b3739b0ec11adb` |
| research/API_CONTRACT_REVALIDATION.md | 1,763 | `495235b475226935bb7aeb5392c7d1b8a1571178e0bad31c19a8efeef696448f` | `13f244f73e7cfc863f6a06046094bd4599b3cec9` |
| research/E001_SMOKE_PROTOCOL.md | 4,532 | `8684d20b3e1c8ce085ab4dbf7ea54931a8d5697b367719465a93ea4cb0f7f181` | `436edb494deb34567b1841c36eeaed091fcff6c0` |
| research/E001_SMOKE_RESULT.md | 479 | `b2e99a8d657d637593ce0267d375888a31684c6c55faf591a5cb1a6fd222e73d` | `17268372f629b37d5d1ea6a7060a406fcb7a7831` |
| src/kalshi_mm/api.py | 6,010 | `4c1a236f453a0726107facca35dd33d770c5720185ba2481ea3e51a0a0ad2d37` | `ff9f17f3ce25b17d959de754169a2e2cbf77d2e3` |

The original encoded bundle object itself is 10,000 bytes, SHA-256
`576416507e311e0d03acbd79021a19ae191e2f904b1ff94b00c3be785a6ea790`,
Git blob `673f0cf8f1f432c2a5d720df1b62dd5a6a82c49a`.

## Materially missing prior implementation

The prior implementation described modules for fixed-point parsing, time handling, market metadata,
prospective collection, frozen policy mechanics, raw immutable storage, deterministic replay,
integrity validation, and production preflight. Exact prior files for those modules were not recovered.
No exact prior collector test suite was recovered. The prior handoff stated 28 focused tests; those
tests are absent from the recovered objects.

The base commit's older `src/` and two older tests remain in GitHub history, but they are foundation
files and are not evidence that the later collector implementation was recovered.

## Validation gate

Stage-7 source validation was not run because the exact source tree is incomplete. A `compileall`
command over the nine complete tar members returned 0, but those members contain no recovered Python
implementation source and that result is not treated as source validation.

- complete prior `src/`: NO
- complete prior `tests/`: NO
- workflows/tooling complete: NO
- any recovered file truncated: YES, the tar copy of SECURITY.md
- full implementation Python compilation: NOT RUN
- pytest collection: NOT RUN
- pytest result: NOT RUN
- missing code reconstructed: NO

The tar-contained and separately dangling segment-workflow variants are both preserved. No attempt was
made to choose, merge, or rewrite them.

## Preserved recovery artifacts

- partial-stream artifact: GitHub Actions artifact `10595960378`
  (`e001-partial-recovery-35479712486`)
- known-object artifact: GitHub Actions artifact `10595432513`
  (`e001-known-dangling-objects-35479869552`)

Exact next step: obtain the missing exact original worktree/archive chunks or exact Git object IDs from
another preserved source. Do not resume publication, CI, production preflight, smoke, or E001 until the
missing prior source and tests are recovered exactly.
