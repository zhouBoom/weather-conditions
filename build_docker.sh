#!/bin/bash
NAMESPACE="${1:-codebase_b2961_app}"
docker build -t "$NAMESPACE" .