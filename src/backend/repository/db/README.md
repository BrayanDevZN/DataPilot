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
