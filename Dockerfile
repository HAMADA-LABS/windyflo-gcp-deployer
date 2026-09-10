ARG DEPLOYER_BASE=gcr.io/cloud-marketplace-tools/k8s/deployer_helm@sha256:60bc54af5578550df364109be383ea575ea97fdcae4c8236398f8647a5f75bee
FROM ${DEPLOYER_BASE}
COPY windyflo.tar.gz /data/chart/windyflo.tar.gz
COPY schema.yaml /data/schema.yaml
ENV WAIT_FOR_READY_TIMEOUT=1800 TESTER_TIMEOUT=1800
