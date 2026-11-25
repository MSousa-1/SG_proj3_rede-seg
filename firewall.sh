#!/bin/sh
set -eu

nft -f - <<'RULES'
flush ruleset
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;
    ct state established,related accept
    iifname "lo" accept
    tcp dport { 8080, 8443 } accept
    log prefix "LAB_FIREWALL_BLOCK: " counter drop
  }
  chain output {
    type filter hook output priority 0; policy drop;
    ct state established,related accept
    oifname "lo" accept
  }
}
RULES

exec "$@"
