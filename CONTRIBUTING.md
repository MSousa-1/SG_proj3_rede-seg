# Contribuindo

Este documento define as convenções do projeto para código, documentação,
testes e organização do repositório. As regras se aplicam a contribuições novas
e modificadas.

## Idioma

Escreva código-fonte, identificadores, comentários, docstrings, testes,
mensagens de commit e documentação do projeto em inglês por padrão. Mantenha
`README.md` e `CONTRIBUTING.md` em português. Use outro idioma para os demais
conteúdos somente quando houver uma necessidade específica de público ou de uma
interface voltada ao usuário.

## Estilo Python e verificações estáticas

- Use Python 3.12 ou mais recente.
- Use `snake_case` para funções, métodos e variáveis; `PascalCase` para classes
  e `UPPER_SNAKE_CASE` para constantes de módulo.
- Escreva docstrings para todos os módulos e funções ou métodos públicos. Use
  inglês e descreva o propósito, os argumentos, os valores de retorno e as
  exceções quando não forem evidentes.
- Use [Ruff](https://docs.astral.sh/ruff/) para lint e formatação. A configuração
  está em `pyproject.toml`; não desative regras sem uma justificativa clara.
  Nomes exigidos por frameworks, como `do_GET` e `do_POST`, estão isentos da
  verificação de nomenclatura de métodos em `app.py`.

Instale o Ruff no ambiente de desenvolvimento e execute estas verificações na
raiz do repositório:

```sh
python -m pip install ruff
ruff check .
ruff format --check .
```

Se a verificação indicar alterações, formate o código com `ruff format .` antes
de enviar a contribuição.

## Testes

Adicione ou atualize testes quando houver mudanças de comportamento. A suíte de
integração verifica HTTP, HTTPS, autenticação, HMAC, validação TLS e regras do
firewall. Execute-a com Docker Compose após gerar os certificados locais:

```sh
./scripts/generate-certs.sh
docker compose up --build -d gateway
docker compose --profile test run --rm test-client
docker compose --profile test down
```

Não inclua no commit certificados gerados, capturas de pacotes ou outros
artefatos locais.

## Estrutura do repositório

Mantenha o projeto enxuto e organize os arquivos novos por responsabilidade. A
estrutura prevista é:

```text
.
├── app.py                  # Aplicação HTTP/HTTPS e serviço de auditoria
├── firewall.sh             # Firewall do gateway e inicialização de processos
├── compose.yaml            # Serviços e redes do laboratório local
├── Dockerfile              # Imagem de execução
├── pyproject.toml          # Configuração das ferramentas Python
├── README.md               # Visão geral e instruções de uso
├── CONTRIBUTING.md         # Convenções para contribuições
├── scripts/                # Scripts de certificados e manutenção
├── tests/                  # Testes automatizados
└── docs/                   # Notas de projeto e relatórios, quando necessário
```

Mantenha o código da aplicação na raiz enquanto ela for um único serviço
pequeno. Se crescer e passar a ter vários módulos, mova a implementação para um
pacote próprio (por exemplo, `src/`) e atualize em conjunto a imagem Docker e
os testes. Coloque automações reutilizáveis em `scripts/`, testes em `tests/` e
documentação complementar em `docs/`; não crie diretórios sem uma necessidade
concreta.
