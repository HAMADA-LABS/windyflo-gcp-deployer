#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import tarfile
with tarfile.open('windyflo.tar.gz', 'w:gz') as tar:
    tar.add('chart', arcname='chart')
PY
docker build --platform linux/amd64 -t windyflo-gcp-deployer-review:3.0.14 .
docker run --rm --platform linux/amd64 --network none \
  -v "$PWD/verify_deployer.py:/verify_deployer.py:ro" \
  --entrypoint python3 windyflo-gcp-deployer-review:3.0.14 /verify_deployer.py
