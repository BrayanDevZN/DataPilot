# Models ORM

`Base` herda `sqlalchemy.orm.DeclarativeBase`. Cada tabela possui um arquivo em
`models/`. Importe `src.backend.repository.db.models` para registrar os 11 models
no mesmo `Base.metadata`. Os imports não conectam ao banco nem criam tabelas.

```python
from src.backend.repository.db.base import Base
from src.backend.repository.db.models import User, Dashboard
```

A base registra a definição dos models e a construção de objetos usando o logger
global, sem registrar valores dos atributos. Os models não fazem CRUD.

## Origem do esquema

Mapeamento baseado nas consultas do DATABASE_AI (`c98ebea`) e migrations
recuperadas de `a6daf2f^`. Colaboração, notificações, username e extensão de fontes
possuem definições SQL versionadas. As demais tabelas não possuem DDL completo
no histórico consultado: tipos, nulabilidade, defaults e ações de exclusão foram
reconstruídos a partir do uso e devem ser conferidos com o schema real antes de
qualquer migration. Em particular, `validation.validation_id` é a chave primária
inferida; os códigos foram representados como `String(6)` para preservar zeros.

Os dados/configurações dos gráficos e fontes usam JSONB. Datas usam TIMESTAMP sem
fuso, como as migrations existentes. `onupdate=func.now()` atua nas atualizações
feitas pelo SQLAlchemy; não cria um trigger no banco.

## Criação das tabelas

`Migration` recebe um `AsyncEngine` e carrega todos os models antes de executar
`Base.metadata.create_all` via `run_sync`, dentro de `engine.begin()`:

```python
from src.backend.repository.db.migrate import Migration

# engine é o AsyncEngine obtido pela infraestrutura.
await Migration(engine)()
```

O `__call__` coordena `create_tables()` e `load_models()`. Todas as etapas registram
logs; falhas são propagadas. A classe usa o engine recebido e não o encerra.
`checkfirst=True` evita recriar tabelas existentes. Este processo cria tabelas
ausentes, mas não altera colunas ou constraints de tabelas existentes; evolução
versionada do esquema exige migrations específicas.

## Relacionamentos

Os models têm relações bidirecionais com `back_populates`. Exemplos:
`User.conversations`, `Conversation.messages`, `DataSource.dashboards`,
`Dashboard.charts`, `Dashboard.collaborations`, `DashboardChart.settings`.
A colaboração diferencia `owner` e `collaborator` com suas respectivas chaves.
`ValidationAccount` permanece sem relação com usuário, pois antecede o cadastro.

Use carregamento explícito nas consultas assíncronas:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.backend.repository.db.models import Dashboard

query = select(Dashboard).options(selectinload(Dashboard.charts))
```

`lazy="raise"` impede consultas implícitas ao acessar uma relação não carregada.
`passive_deletes="all"` nas relações parentais delega as ações de exclusão às
foreign keys do banco, sem adicionar regras de delete-orphan no ORM. A estrutura
de colunas/constraints permanece igual; relationships não exigem migration.

## Controles por tabela

`control/` contém um arquivo com o nome de cada tabela e uma classe correspondente.
A implementação comum fica em `control_base.py`, fora de `control/`, para manter
os contratos de CRUD, filtros e transações consistentes. Cada classe recebe
`session: AsyncSession`; nenhuma cria uma sessão. Cada operação abre `async with session.begin()` quando
não há transação explícita ativa; esse contexto confirma ou reverte a operação.
Os controles usam SQLAlchemy e retornam somente colunas em dicionários, sem
objetos ORM ou carregamento implícito de relações. Datas continuam como datetime.

```python
from src.backend.repository.db.control import UsersControl, ConversationsControl

async def create_account_and_conversation(session_factory):
    async with session_factory() as session, session.begin():
        user = await UsersControl(session).create({
            "name": "Brayan", "username": "brayan", "email": "brayan@example.com",
            "password": "HASH_JA_GERADO", "age": 18, "gender": "other",
        })
        return await ConversationsControl(session).create({
            "user_id": user["item"]["user_id"], "title": "Primeira conversa",
        })
```

Cada método público usa o gerenciador de contexto `session.begin()`. Quando o
chamador já abriu uma transação explícita, o método participa dela sem fazer
commit independente. Assim, o exemplo acima continua atômico entre tabelas.
Chamadas isoladas também funcionam: `await UsersControl(session).create(data)`.
Não capture uma exceção para continuar uma transação externa abortada.

Um SELECT feito diretamente na sessão pode iniciar autobegin: finalize essa
transação antes de usar um controle. O controle não confirma operações externas
implicitamente. Cada tarefa/requisição usa sua própria AsyncSession.

### Contratos comuns

| Método | Resultado |
| --- | --- |
| `create(data)` | `{"item": {...}}` |
| `get(id, filters=..., for_update=False)` | `{"found": bool, "item": dict ou None}` |
| `list(filters=..., limit=100, offset=0)` | `{"items": [...], "count": quantidade da página}` |
| `update(id, data, filters=..., expected=...)` | `{"updated": bool, "item": dict ou None}` |
| `delete(id, filters=..., expected=...)` | `{"deleted": bool, "id": id ou None}` |

Filtros usam igualdade de colunas. `expected` também participa do WHERE: use-o
para comparar a versão/valor lido antes de atualizar ou excluir. Zero linhas
significa registro ausente, filtro incompatível ou versão antiga; não há nova
consulta para distinguir esses casos. PKs não podem ser fornecidas na criação;
PKs, foreign keys e timestamps de criação não podem ser reatribuídos na atualização.
Atualizações de tabelas com `updated_at` usam o relógio atual do banco.

| Controle | Operações específicas |
| --- | --- |
| `UsersControl` | E-mail/username normalizados; busca por e-mail ou username. |
| `ValidationControl` | `issue` e `consume`, com lock do usuário e consumo único. |
| `ValidationAccountControl` | `issue` e `consume`, com lock transacional por e-mail. |
| `ConversationsControl` | Listar, buscar e excluir por proprietário. |
| `MessagesControl` | `append` valida proprietário e atualiza a conversa na mesma transação; listagem por conversa/usuário. |
| `DataSourcesControl` | Listar por usuário, `claim_due` e `finish_sync` com token de reserva. |
| `DashboardsControl` | Listar por usuário, leitura consistente com gráficos, `finish_refresh`, marcar vinculados como desatualizados. |
| `DashboardChartsControl` | Listar por dashboard e `replace_all` com savepoint. |
| `DashboardChartSettingsControl` | `save` via UPSERT para configurações do dashboard ou de um gráfico. |
| `DashboardCollaborationsControl` | `invite` via UPSERT; `respond` altera apenas um convite ainda pending. |
| `CollaborationNotificationsControl` | Listar por destinatário, marcar uma ou todas como lidas. |

### Concorrência e transações compostas

UPDATE/DELETE usam uma única instrução com RETURNING. Alterações nos gráficos,
configurações e colaborações usam o dashboard como lock comum. Locks múltiplos
são adquiridos em ordem de ID quando o método atualiza diversos dashboards. Ao
compor outras operações, mantenha uma ordem consistente dos locks; deadlocks e
falhas de serialização devem ser tratados pelo chamador com retry da transação
inteira, nunca pelo controle com retry parcial. `IntegrityError` é propagado;
o contexto da transação faz rollback. Não capture e continue uma transação
abortada, salvo quando a operação usou um savepoint explicitamente.

`finish_refresh` exige `expected_updated_at`: capture a versão antes de chamar a
IA e use-a para impedir que uma resposta antiga sobrescreva uma atualização nova.
A substituição dos charts e a atualização do dashboard são atômicas. `replace_all`
usa savepoint: se a inserção falhar, os charts antigos permanecem mesmo que o
chamador capture a exceção. Configurações específicas dos charts apagados seguem
o ON DELETE CASCADE dos models.

Para sincronização, `claim_due` usa FOR UPDATE SKIP LOCKED e avança `next_sync_at`
pelo prazo da reserva. **Encerre/confirme essa transação antes do acesso externo**.
Use o `next_sync_at` retornado como `expected_next_sync_at` em `finish_sync`, em
uma nova transação. A conclusão verifica também se o prazo não expirou. Um worker
com reserva antiga não pode sobrescrever o resultado de um worker novo. Falhas
podem ser retomadas quando a reserva expirar. A reserva não cria um scheduler.

Consumo de código e criação de conta/troca de senha devem ocorrer na **mesma
transação**, para não perder o código se a operação seguinte falhar. Envio de
mensagens/e-mails e chamadas à IA ficam fora das transações que mantêm locks.

CRUD genérico recebe dados/filtros confiáveis do caso de uso; não é uma API de
permissões. Autorização e validação do payload ficam nas próximas camadas. Use os
métodos especializados para os fluxos descritos acima. Os dicts do repository
podem conter hashes de senha e connection_config: não os exponha diretamente nas
respostas HTTP. Os logs não registram argumentos nem conteúdo dos registros.

### Constraints necessárias no banco existente

Os models incluem os índices únicos `users_email_lower_unique` e
`dashboard_chart_settings_dashboard_default_unique` (este último apenas para
chart_id NULL). PostgreSQL garante a unicidade inclusive entre processos.
`Migration.create_tables` instala-os em tabelas novas, mas não atualiza tabelas
existentes. O SQL em `control_constraints.sql` prepara esses dois índices no banco
existente; não foi executado em produção. Corrija duplicatas existentes antes de
aplicá-lo. Os demais FKs/constraints dos models também precisam existir no schema.

### Testes locais

```bash
pip install -r tests/integration/requirements.txt
python tests/integration/db_control.py
```

O script inicia um PostgreSQL temporário local, cria um schema privado por teste,
valida CRUD, rollback e disputas entre sessões independentes, e remove apenas
os próprios schemas. Não usa o .env nem credenciais de produção. O pacote
`pgserver` precisa ter um wheel compatível com a plataforma/Python usado.
