#!/bin/bash

gcloud preview container clusters create cluster-test --cluster-api-version 0.12.0 --machine-type f1-micro --num-nodes 2
gcloud preview container kubectl create --validate -f api-service.json
gcloud preview container kubectl create --validate -f screen-service.json
gcloud preview container kubectl create --validate -f worker-service.json
