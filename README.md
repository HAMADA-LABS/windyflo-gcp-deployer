# WindyFlo for GCP deployment assets

This repository contains the Kubernetes deployment chart, Google Cloud Marketplace deployer schema, build instructions, and local validation for WindyFlo BYOL version 3.0.14.

The Marketplace listing is being prepared. The container images below are in the publisher's staging registry and require authorized registry access. A successful local validation does not establish a successful GKE installation or Marketplace certification.

## Requirements

- A WindyFlo license obtained directly from HamadaLabs for the intended BYOL deployment. Contact [WindyFlo](https://windyflo.com) for licensing and support.
- An existing GKE Standard cluster with Linux amd64 nodes and Persistent Disk CSI enabled.
- CloudNativePG 1.24, MinIO Operator 6, an NGINX ingress controller, and cert-manager already installed. This chart deploys database and object-storage instances managed by those operators; it does not install the operators.
- An existing, ready cert-manager ClusterIssuer and a DNS name that you control.
- Docker, kubectl, and Google's [mpdev deployment tools](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md).
- Kubernetes permissions to create the resources defined by the chart in the target namespace.

Google Cloud infrastructure is billed separately. Review the chart's resource requests and persistent storage sizes before deploying: the defaults include three PostgreSQL instances, four MinIO storage servers, Redis replication with Sentinel, and multiple application and worker replicas.

## Container images

The staging image prefix is:

```text
us-docker.pkg.dev/windyflo-public/windyflo-marketplace/windyflo
```

The deployer is available at:

```text
us-docker.pkg.dev/windyflo-public/windyflo-marketplace/windyflo/deployer:3.0.14
```

Its immutable manifest digest is:

```text
sha256:00bbfbad8fa7250e5f7494f2e316af66d4ac50de3cfaa916540bb4624299d332
```

The release track is `3.0`. All seven application images use the same `3.0.14` version tag and `3.0` track tag. `images.json` records their immutable manifest digests. After Marketplace publication, use the deployer location shown on the Marketplace product page; Google's public image location can differ from this staging prefix.

## Command-line deployment

First configure kubectl for the target cluster using the Google Cloud CLI and verify the active context:

```sh
gcloud container clusters get-credentials YOUR_CLUSTER \
  --location YOUR_LOCATION --project YOUR_GCP_PROJECT
kubectl config current-context
kubectl get crd clusters.postgresql.cnpg.io tenants.minio.min.io clusterissuers.cert-manager.io
kubectl get ingressclass nginx
kubectl get clusterissuer YOUR_TLS_ISSUER
```

For staging evaluation, your account and the cluster's image-pull identity must be authorized to read the publisher's Artifact Registry. Set up the [mpdev tool](https://github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/blob/master/docs/mpdev-references.md) and its required Application CRD, and run `mpdev doctor` before installation.

Choose a fresh namespace for each installation. Replace the example DNS name and issuer below with your own values, then run:

```sh
mpdev install \
  --deployer=us-docker.pkg.dev/windyflo-public/windyflo-marketplace/windyflo/deployer@sha256:00bbfbad8fa7250e5f7494f2e316af66d4ac50de3cfaa916540bb4624299d332 \
  --parameters='{"name":"windyflo","namespace":"windyflo","ingress.host":"windyflo.example.com","ingress.tls.issuer":"YOUR_TLS_ISSUER"}'
```

The form also accepts these optional parameters:

| Parameter | Default | Purpose |
| --- | --- | --- |
| `main.autoscaling.maxReplicas` | `8` | Application autoscaling ceiling, from 2 to 16 |
| `worker.autoscaling.maxReplicas` | `8` | Worker autoscaling ceiling, from 2 to 16 |
| `data.postgres.storageClass` | `premium-rwo` | PostgreSQL persistent storage |
| `data.minio.storageClass` | `premium-rwo` | Object-storage persistent storage |
| `redis.global.storageClass` | `premium-rwo` | Redis persistent storage |

The deployer generates the required application secrets. Preserve those secrets and all persistent data when maintaining an installation.

## Verify and open the application

```sh
kubectl -n windyflo get pods,svc,ingress
kubectl -n windyflo get clusters.postgresql.cnpg.io,tenants.minio.min.io
kubectl -n windyflo rollout status deployment/windyflo-main --timeout=1800s
kubectl -n windyflo rollout status deployment/windyflo-worker --timeout=1800s
kubectl -n windyflo port-forward service/windyflo-main 3000:3000
```

In another terminal:

```sh
curl --fail http://127.0.0.1:3000/api/v1/ping
```

Point the chosen DNS name at the existing ingress controller's external address. Verify the TLS certificate is ready before opening `https://YOUR_DOMAIN`. Use [WindyFlo's user guide](https://windyflo.com/user-guide/how-to-build-pipelines) to configure a workflow and supply your own model-provider credentials.

## Build and validate the deployer locally

```sh
./build.sh
```

The build pins Google's official Helm deployer base image by digest. The chart dependencies are vendored, so the deployer does not fetch Helm charts while installing the app.

The local verification checks the schema, Google's configuration expansion and manifest generation, the Application resource, replacement of all seven image locations, and the mapping of form inputs to the resulting Kubernetes resources. It does not create a cluster or establish that the complete application works on GKE.

## Operations and release status

Review `chart/values.yaml` before changing replica counts, storage, backup settings, or secrets. PostgreSQL backup configuration targets the in-cluster object store; validate backup completion and a restoration exercise in your environment before relying on it. Keep the application encryption key with protected backups.

Before publication, complete a GKE install/functionality/uninstall verification, review image scan findings, confirm the final public partner identifier, and finish Google's container review. BYOL licensing and the customer deployment guide also require the publisher's final review.

Removing the Application resource is the Marketplace uninstall mechanism. Database operators and persistent-volume reclaim policies can retain data; inventory and back up data before any uninstall, and review retained resources separately.

## License

The deployment assets retain the source repository's Apache 2.0 license in `LICENSE.md`. This file does not define or replace the separately agreed WindyFlo BYOL software license.
