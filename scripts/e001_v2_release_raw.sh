#!/usr/bin/env bash
# V2 public GET-only E001 raw-observation transport to GitHub draft Release assets.
# Storage transport ONLY; no broker credentials, orders, synthetic observations,
# economic results, historical backfills, or alteration of the frozen strategy.
set -euo pipefail

operation="${1:?operation required}"
root="${2:-smoke-data}"
chunk="${3:-}"
repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"
commit="${GITHUB_SHA:?GITHUB_SHA required}"
tag="kalshi-e001-v2-${commit:0:12}"

case "$operation" in
  init)
    # Fail on any existing release/tag collision. Never reuse another run's data.
    gh release create "$tag" --repo "$repo" --draft --latest=false \
      --target "$commit" \
      --title "Kalshi E001 V2 read-only verification — $commit" \
      --notes "Public unauthenticated GET-only integrity verification. Official 30-day E001 evidence is NOT running. Data are intentionally unpublished until reviewed. No orders, trading economics or funded execution." 
    ;;
  upload)
    case "$chunk" in 1|2|3|4|5) ;; *) echo "Invalid chunk" >&2; exit 1;; esac
    segment="$root/observations-chunk-$chunk.jsonl.gz"
    test -s "$segment"
    test -s "$root/manifest.json"
    python - "$root/manifest.json" "$segment" <<'PY'
import hashlib, json, pathlib, sys
manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
segment = pathlib.Path(sys.argv[2])
rows = [e for e in manifest["segments"] if e["path"] == segment.name]
if len(rows) != 1 or hashlib.file_digest(segment.open("rb"), "sha256").hexdigest() != rows[0]["sha256"]:
    raise SystemExit("Immutable raw segment does not match manifest; refusing release upload")
PY
    # Files are split well below GitHub's 2 GiB *individual release asset* cap.
    # Never clobber: duplicate names or partial previous upload fail closed.
    split -b 512m -d -a 3 "$segment" "$root/e001-v2-raw-$chunk-part-"
    mapfile -t parts < <(find "$root" -maxdepth 1 -type f \
      -name "e001-v2-raw-$chunk-part-*" | sort)
    test "${#parts[@]}" -ge 1
    (cd "$root" && sha256sum "observations-chunk-$chunk.jsonl.gz" > "e001-v2-raw-$chunk.sha256")
    gh release upload "$tag" "${parts[@]}" "$root/e001-v2-raw-$chunk.sha256" --repo "$repo"
    # Successful upload is required before the next chunk may access its
    # checkpoint state; failure stops the job and the entire chain.
    ;;
  download-all)
    mkdir -p "$root"
    for i in 1 2 3 4 5; do
      gh release download "$tag" --repo "$repo" --dir "$root" \
        --pattern "e001-v2-raw-$i-part-*" --pattern "e001-v2-raw-$i.sha256"
      mapfile -t parts < <(find "$root" -maxdepth 1 -type f \
        -name "e001-v2-raw-$i-part-*" | sort)
      test "${#parts[@]}" -ge 1
      cat "${parts[@]}" > "$root/observations-chunk-$i.jsonl.gz"
      (cd "$root" && sha256sum --check --status "e001-v2-raw-$i.sha256")
      gzip -t "$root/observations-chunk-$i.jsonl.gz"
      # Checksum is verified twice: against the release transport sidecar now
      # and against the collector's frozen manifest during smoke_review replay.
    done
    ;;
  upload-review)
    test -s "$root/smoke-review.json"
    test -s "$root/verification-authorization.json"
    # Leave this as a draft; publishing or deleting immutable evidence requires
    # a separate human governance decision.
    gh release upload "$tag" "$root/smoke-review.json" \
      "$root/verification-authorization.json" --repo "$repo"
    ;;
  *)
    echo "usage: $0 init | upload <root> <chunk> | download-all <root> | upload-review <root>" >&2
    exit 2
    ;;
esac
