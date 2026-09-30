# Infraestrutura do backend

Conexões e configuração. CRUD, migrations e regras de negócio ficam nas outras
camadas. Instale na raiz: `pip install -r src/backend/requirements.txt`.

## Configuração

Copie `core/.env.example` para `src/backend/infra/core/.env` ou para `.env` na raiz.
O arquivo local é selecionado quando existe; na ausência dele, usa-se o da raiz.
Variáveis já definidas no processo têm prioridade. A seleção independe do diretório
de execução. Sem arquivos, são usadas as variáveis do processo.

`DATABASE_URL` prevalece sobre `DB_*`. PostgreSQL/Supabase usa o driver assíncrono
psycopg via `create_async_engine`, preservando parâmetros como `sslmode`.

## Banco assíncrono

`manage.py` disponibiliza `database`, `infra`, `settings` e `connect_database`.
Importar o módulo não abre conexões nem executa consultas.

```python
from src.backend.infra.manage import database, connect_database, infra

async def startup():
    engine, session_factory = await connect_database()
    # Equivalente a: engine, session_factory = await database()
    # Retornos: AsyncEngine e async_sessionmaker[AsyncSession].
    return engine, session_factory

async def shutdown():
    await infra.close()
```

A classe do banco fornece:

- `base_url()`: monta a URL;
- `create_engine()`: cria/reutiliza o `AsyncEngine`;
- `create_session()`: cria/reutiliza a fábrica de `AsyncSession`;
- `await test()`: executa `SELECT 1`, retornando `True` ou propagando a falha;
- `await connection()`: o `__call__` monta os objetos, testa a conexão e retorna
  `(engine, session_factory)`;
- `await close()`: libera o pool.

`test_connection()` é um alias assíncrono de `test()`. Engine e fábrica são
reutilizados; cada chamada à fábrica cria uma sessão independente:

```python
async def repository_operation(session_factory):
    async with session_factory() as session:
        # Consultas/transações do repository usam await session.execute(...).
        pass
```

Repositories recebem a fábrica/engine por injeção. Domínio e casos de uso não
importam esta camada. Sessões não devem ser compartilhadas entre requisições.

## Outros serviços

| Classe | Método de teste | Método que testa e retorna o objeto |
| --- | --- | --- |
| `SQLConnection` | `await connection.test()` | `await connection()` retorna engine e fábrica |

`manage.py` disponibiliza o objeto `sender`, configurado por `EMAIL_USER`,
`EMAIL_PASSWORD` e `EMAIL_TIMEOUT`. Para Gmail, use uma senha de aplicativo.
O envio usa yagmail em uma thread para preservar o loop assíncrono, com um cliente
independente por chamada, encerrado ao concluir ou falhar. A importação não envia
mensagens. Erros de SMTP são propagados e logs não incluem credenciais nem conteúdo.

```python
from src.backend.infra.manage import sender

async def notify():
    return await sender.send("destinatario@example.com", "Assunto", "Mensagem")
```

Banco SQL externo exige um driver compatível com asyncio instalado:

```python
external = infra.external_database("postgresql+psycopg://user:password@host/database",
                                   connect_args={"connect_timeout": 10})
async def use_external():
    try:
        engine, sessions = await external()
    finally:
        await external.close()
```

Validação de fontes fornecidas pelo usuário (permissões, URLs públicas, consultas
permitidas e limites) fica no adapter/caso de uso antes de chamar o transporte.

## Logs

A configuração global está em `src/backend/logs/log.py`:

```python
from src.backend.logs.log import logger

logger.info("Iniciando operação")
```

Os métodos da infraestrutura registram início, conclusão e falhas no terminal e
em `src/backend/logs/app.log`. O caminho independe do diretório de execução.
O arquivo usa rotação de 5 MiB com três backups. Logs e backups estão no
`.gitignore` da raiz. Argumentos, resultados e mensagens de exceção não são
registrados automaticamente, para evitar expor credenciais.
