# Controles com banco e cache

Cada tabela possui uma classe `ControlNomeDaTabela`, que recebe
`redis.asyncio.Redis` e `AsyncSession`. Os métodos são assíncronos e têm logs:

- `insert(data)` grava no banco, confirma a transação e armazena o registro no cache.
- `select(identifier, value)` retorna o registro do cache ou consulta o banco;
  um resultado encontrado é armazenado, e uma busca sem resultado retorna `None`.
- `update(identifier, value, data)` atualiza o banco e invalida o cache; retorna
  o registro atualizado ou `None` quando não existe.
- `delete(identifier, value)` exclui o registro e invalida o cache, retornando
  o dicionário `deleted`/`id` do controle de banco.

```python
from src.backend.repository.control import ControlUsers

async def example(redis_client, session, public_id):
    users = ControlUsers(redis_client, session)
    user = await users.select("public_id", public_id)
    return user
```

As chaves seguem `tabela:identificador:valor`, por exemplo
`users:public_id:550e8400-e29b-41d4-a716-446655440000`. São aceitos a chave
primária, `public_id` quando disponível e email/username para users. Valores
UUID e datetime são preservados no retorno, inclusive ao ler do cache.

`Cache` usa TTL padrão de 60 segundos para set, hash e incr, aplicado na mesma
transação Redis. Atualizações invalidam as chaves alternativas da tabela;
exclusões invalidam também os caches que podem ser afetados por FK/cascatas.

Os controles administram e confirmam suas próprias transações. A sessão deve
estar sem transação ativa ao entrar, e cada tarefa deve usar uma sessão própria.
Não use `session.begin()` externo nesses controles: dados não confirmados não
devem ser publicados no cache. Operações agrupadas continuam disponíveis nos
controles de `db/control`, que não administram cache.

Um lock Redis compartilhado coordena leituras, preenchimentos e invalidações,
com renovação durante a operação e liberação pelo contexto. A estratégia é
conservadora e serializa essas operações; pode ser refinada quando o volume
exigir. Escritas feitas diretamente nos controles de banco não invalidam este
cache. Falhas de banco e Redis são propagadas; banco e Redis não têm commit
distribuído. Uma falha Redis após o commit não desfaz a gravação no banco.
