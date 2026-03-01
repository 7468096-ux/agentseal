#!/bin/bash
set -e
HOST="root@3.0.92.255"
ssh $HOST "cd /opt/agentseal && git pull && docker compose build && docker compose up -d"
