# Ambiente de Rede com Políticas de Segurança

Laboratório reproduzível de uma pequena rede corporativa isolada para comparar
HTTP e HTTPS, testar autenticação e integridade HMAC, aplicar filtragem de
tráfego e capturar pacotes. É uma demonstração didática: não use as credenciais,
chaves ou certificados do laboratório em produção.

## Arquitetura

```text
Host (somente loopback) ── HTTP :8080 / HTTPS :8443 ── gateway
                                                       ├── firewall nftables
Cliente de teste ──────────────────────────────────────┤
Captura tcpdump (namespace do gateway) ────────────────┘
```

O Compose cria uma rede bridge dedicada. O gateway disponibiliza o serviço HTTP em
`127.0.0.1:8080` e HTTPS em
`127.0.0.1:8443`. O HTTPS usa certificado de laboratório assinado por uma CA
local; o cliente de teste confia nessa CA. O serviço de auditoria TCP na porta
9000 existe para demonstrar que o firewall bloqueia tráfego não autorizado.
As portas publicadas aceitam conexões do host local; nftables também bloqueia
conexões iniciadas pelo gateway para redes externas.

## Requisitos

- Docker com Docker Compose v2 e suporte a `NET_ADMIN`/`NET_RAW`.
- OpenSSL e curl no host.
- Linux recomendado para consultar os registros do firewall no kernel.

## Iniciar e reproduzir

Na raiz do repositório:

```sh
./scripts/generate-certs.sh
docker compose up --build -d gateway
```

Verifique a disponibilidade e o certificado:

```sh
curl http://localhost:8080/
curl --cacert certs/ca.crt https://localhost:8443/
openssl x509 -in certs/server.crt -noout -subject -issuer -ext subjectAltName
```

O certificado é confiável somente quando o cliente recebe explicitamente
`certs/ca.crt`; não desative a validação TLS (`-k`) no experimento de validação.
Para observar credenciais/dados em claro no HTTP, faça o teste autenticado:

```sh
curl -u aluno:rede-segura-2026 http://localhost:8080/protected
curl --cacert certs/ca.crt -u aluno:rede-segura-2026 \
  https://localhost:8443/protected
```

As credenciais e a chave HMAC acima são valores exclusivos do laboratório e
podem ser sobrescritos pelas variáveis `LAB_USER`, `LAB_PASSWORD` e
`LAB_HMAC_KEY` antes de iniciar os serviços. O endpoint `/protected` requer
autenticação HTTP Basic; no HTTP, inclusive o cabeçalho de autenticação fica
visível na captura. HTTPS protege o conteúdo em trânsito.

### Integridade HMAC

O endpoint `POST /hmac` exige autenticação e recebe JSON com `message` e
`signature`. A assinatura é HMAC-SHA256 hexadecimal da mensagem, calculada com
`LAB_HMAC_KEY`. O serviço compara assinaturas em tempo constante e rejeita
assinaturas inválidas com HTTP 400. A chave compartilhada é apenas para
demonstração e nunca é enviada na requisição.

```sh
MESSAGE='mensagem de laboratório'
SIGNATURE=$(printf %s "$MESSAGE" |
  openssl dgst -sha256 -hmac 'chave-laboratorio-nao-usar-em-producao' |
  awk '{print $NF}')
curl -u aluno:rede-segura-2026 -H 'Content-Type: application/json' \
  -d "{\"message\":\"$MESSAGE\",\"signature\":\"$SIGNATURE\"}" \
  http://localhost:8080/hmac
```

Altere a mensagem sem recalcular a assinatura e repita a requisição para
demonstrar a detecção de alteração. O teste automatizado faz os casos válido e
inválido nos dois protocolos.

### Firewall, monitoramento e testes

As regras nftables aceitam loopback, conexões estabelecidas e TCP nas portas
8080/8443. O restante do tráfego de entrada é registrado no kernel e descartado.
O teste conecta à porta de auditoria 9000 e confirma que ela não é alcançável.

```sh
docker compose --profile test run --rm test-client
docker compose --profile capture up -d capture
curl -u aluno:rede-segura-2026 http://localhost:8080/protected
curl --cacert certs/ca.crt -u aluno:rede-segura-2026 \
  https://localhost:8443/protected
docker compose --profile capture stop capture
```

A captura é gravada em `captures/lab.pcap` (diretório ignorado pelo Git). Abra-a
no Wireshark ou use `tcpdump -nn -A -r captures/lab.pcap` para verificar que
requisições HTTP podem ser lidas e o conteúdo HTTPS não. Analise também o
ClientHello, a negociação TLS e o certificado. Para observar descartes no host
Linux, acompanhe `sudo journalctl -k -f | grep LAB_FIREWALL_BLOCK`; consulte
`sudo nft list ruleset` para a política e os contadores. A captura contém dados
de teste; remova-a ao terminar.

Resultados automatizados: autorização válida em HTTP e HTTPS, negação sem
credenciais, HMAC válido e alterado, validação do certificado TLS e bloqueio da
porta não autorizada.

## Plano de trabalho da equipe (4 programadores)

| Responsável | Escopo | Prazo |
| --- | --- | --- |
| Programador 1 — Scrum Master/integração | Topologia, critérios de aceite, integração e acompanhamento do cronograma | 25/11–03/12 |
| Programador 2 — Rede e segurança | Compose, isolamento da rede, nftables e testes de portas permitidas/bloqueadas | 25/11–28/11 |
| Programador 3 — Aplicação | Serviço HTTP/HTTPS, certificado TLS, autenticação e testes de acesso | 26/11–29/11 |
| Programador 4 — Monitoramento | Captura tcpdump, análise HTTP/TLS e experimento HMAC | 26/11–30/11 |
| Toda a equipe | Integração e execução dos experimentos; corrigir pendências | 01/12 |
| Programadores 1 e 4 | Relatório técnico (até 10 páginas), evidências e conclusões | 01/12–02/12 |
| Toda a equipe | Ensaiar apresentação de 15 minutos e demonstração de pelo menos 3 experimentos | 02/12 |
| Toda a equipe | Entrega final e janela para perguntas (5 minutos) | 03/12 |

## Limpeza

```sh
docker compose --profile capture --profile test down
rm -rf certs captures
```
