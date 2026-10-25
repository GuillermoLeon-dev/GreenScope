#!/usr/bin/env bash
# Uso: crono.sh <start|stop> <etapa>  -> registra marca temporal ISO en UTC (inmune a cambios de hora) en cronometro.log
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "$2,$1,$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DIR/cronometro.log"
tail -n1 "$DIR/cronometro.log"
