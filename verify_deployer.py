#!/usr/bin/env python3
"""Runs inside the deployer image. Verifies rendering without contacting a cluster."""
from pathlib import Path
import json
import os
import subprocess
import yaml

schema = yaml.safe_load(Path('/data/schema.yaml').read_text())
prefix = 'marketplace.gcr.io/verification-fixture/windyflo'
parameters = {
    '__image_repo_prefix__': prefix,
    'name': 'wf-verification', 'namespace': 'wf-verification',
    'ingress.host': 'wf-verification.example.com',
    'ingress.tls.issuer': 'verification-issuer',
    'main.autoscaling.maxReplicas': 6, 'worker.autoscaling.maxReplicas': 5,
    'data.postgres.storageClass': 'verification-ssd',
    'data.minio.storageClass': 'verification-ssd',
    'redis.global.storageClass': 'verification-ssd',
}
Path('/data/values.yaml').write_text(yaml.safe_dump(parameters))
subprocess.run(['/bin/validate_schema.py'], check=True)
subprocess.run(['/bin/expand_config.py', '--values_mode=raw'], check=True)
environment = dict(os.environ, NAME=parameters['name'], NAMESPACE=parameters['namespace'])
run = subprocess.run(['/bin/create_manifests.sh'], env=environment, text=True, capture_output=True)
if run.returncode:
    print(run.stderr[-4000:])
    raise SystemExit(run.returncode)
manifest = Path('/data/manifest-expanded/windyflo.yaml')
subprocess.run(['/bin/validate_app_resource.py', '--manifests', str(manifest)], check=True)
resources = [r for r in yaml.safe_load_all(manifest.read_text()) if r]
refs = []
def walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('image', 'imageName') and isinstance(item, str):
                refs.append(item)
            walk(item)
    elif isinstance(value, list):
        for item in value:
            walk(item)
walk(resources)
assert refs and all(ref.startswith(prefix) for ref in refs), sorted(set(refs))
application = next(r for r in resources if r.get('kind') == 'Application')
assert application['metadata']['name'] == parameters['name']
ingress = next(r for r in resources if r.get('kind') == 'Ingress')
assert ingress['spec']['rules'][0]['host'] == parameters['ingress.host']
assert ingress['metadata']['annotations']['cert-manager.io/cluster-issuer'] == parameters['ingress.tls.issuer']
hpas = {r['metadata']['name']: r['spec']['maxReplicas'] for r in resources if r.get('kind') == 'HorizontalPodAutoscaler'}
assert hpas['wf-verification-main'] == 6 and hpas['wf-verification-worker'] == 5, hpas
pg = next(r for r in resources if r.get('kind') == 'Cluster')
assert pg['spec']['storage']['storageClass'] == 'verification-ssd'
result = {'schema_validation': 'passed', 'google_deployer_render': 'passed',
          'application_validation': 'passed', 'image_relocation': 'passed',
          'form_parameter_mapping': 'passed', 'resources': len(resources),
          'distinct_images': len(set(refs)), 'gke_installation': 'not_run'}
print(json.dumps(result, indent=2))
