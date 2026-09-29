# Infraestrutura do backend

Esta camada configura conexões. CRUD, migrations, leitura de tabelas, tratamento de
arquivos e regras de negócio serão implementados nas próximas camadas.

## Configuração

Na raiz do DataPilot, instale `pip install -r src/backend/requirements.txt`.
Copie `core/.env.example` para `src/backend/infra/core/.env` ou para `.env` na raiz.
O arquivo local é selecionado quando existe; somente na ausência dele é usado o
arquivo da raiz. A seleção independe do diretório de execução. Variáveis já
definidas no processo têm prioridade. Sem arquivos, são usadas as variáveis do
processo. Credenciais não são incluídas na representação de `Settings`.

## Uso nas próximas camadas

Execute o backend como pacote a partir da raiz do projeto:

```python
from src.backend.infra.manage import database, infra, settings

engine = database.engine  # engine compartilhado; não abre a conexão neste acesso
database.test_connection()  # SELECT 1; True ou exceção

# Um repository poderá receber esse engine por injeção no seu construtor.
# O domínio e os casos de uso não devem importar infra.
```

`manage.py` monta `infra` e exporta `database`. Não faz consultas, cria tabelas ou
testa serviços ao ser importado. Credenciais ausentes de PostgreSQL/Resend são
validadas quando o respectivo recurso é utilizado.

| Objeto/classe | Uso | Teste explícito |
| --- | --- | --- |
| `database` / `PostgreSQLConnection` | PostgreSQL/Supabase, via psycopg | `test_connection()` executa `SELECT 1` |
| `SQLConnection` | Banco SQL externo, com driver correspondente instalado | `test_connection()` executa `SELECT 1` |
| `infra.http` / `HTTPConnection` | Transporte para APIs externas | `test_connection(url)` faz GET |
| `infra.ai` / `AIConnection` | Transporte para a API de IA | `test_connection()` acessa `AI_HEALTH_PATH` |
| `infra.email` / `ResendConnection` | Transporte autenticado para Resend | `test_connection()` consulta `/domains` |

Os testes HTTP exigem resposta 2xx e propagam falhas; não enviam e-mails nem geram
análises. O teste Resend exige permissão de leitura de domínios: uma chave restrita
a envio pode receber 403 mesmo sendo válida para enviar. `/docs` testa apenas a
disponibilidade HTTP da IA, não o modelo; ajuste o caminho para um healthcheck
quando esse endpoint existir no serviço.

`DATABASE_URL`, se definido, prevalece sobre os campos `DB_*` e usa o driver
`postgresql+psycopg`, preservando parâmetros como `sslmode`.

```python
external = infra.external_database("postgresql+psycopg://user:password@host/database",
                                   connect_args={"connect_timeout": 10})
try:
    external.test_connection()
finally:
    external.close()
```

Chamadas HTTP usam `request(method, path, **kwargs)`; caminhos são relativos ao
serviço para IA/Resend e URLs absolutas para `infra.http`. Validação das fontes
fornecidas por usuários (permissões, URLs públicas, consultas permitidas e limites
de dados) deve ocorrer no adapter/caso de uso antes de chamar o transporte.

No encerramento do aplicativo, chame `infra.close()` para liberar o pool principal.
Conexões retornadas por `database.connect()` devem ser fechadas pelo chamador.

## Verificação local

`python -m unittest discover -s src/backend/tests -v`

Os testes usam SQLite e HTTP simulado, sem acessar serviços de produção.
