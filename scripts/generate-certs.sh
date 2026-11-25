#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
mkdir -p certs
umask 077

openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 365 \
  -keyout certs/ca.key -out certs/ca.crt \
  -subj '/CN=SG Rede Segura Lab CA'
openssl req -new -newkey rsa:2048 -sha256 -nodes \
  -keyout certs/server.key -out certs/server.csr \
  -subj '/CN=gateway'
cat > certs/server.ext <<'EOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:gateway,DNS:localhost,IP:127.0.0.1
EOF
openssl x509 -req -sha256 -days 365 \
  -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.crt -extfile certs/server.ext
rm certs/server.csr certs/server.ext certs/ca.srl
printf 'Certificados de laboratório criados em %s/certs\n' "$PWD"
