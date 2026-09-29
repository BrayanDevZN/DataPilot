# DataPilot Frontend

[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=0f172a)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES_Modules-F7DF1E?style=for-the-badge&logo=javascript&logoColor=0f172a)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![React Router](https://img.shields.io/badge/React_Router-SPA-CA4245?style=for-the-badge&logo=reactrouter&logoColor=white)](https://reactrouter.com/)
[![Recharts](https://img.shields.io/badge/Recharts-Data_Viz-22c55e?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://recharts.org/)
[![Lucide](https://img.shields.io/badge/Lucide-Icons-F56565?style=for-the-badge&logo=lucide&logoColor=white)](https://lucide.dev/)
[![npm](https://img.shields.io/badge/npm-Scripts-CB3837?style=for-the-badge&logo=npm&logoColor=white)](https://www.npmjs.com/)

Frontend web do DataPilot AI, um SaaS de Business Intelligence com IA para transformar fontes de dados em dashboards, graficos, insights executivos, colaboracao e conversas orientadas por contexto.

A aplicacao conecta a experiencia do usuario com dois servicos backend: a API de contas/dados, responsavel por autenticacao e persistencia, e a API de IA, responsavel por interpretar prompts, gerar dashboards e produzir analises em linguagem natural.

## Indice

- [Visao geral](#visao-geral)
- [Como o SaaS funciona](#como-o-saas-funciona)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Principais funcionalidades](#principais-funcionalidades)
- [Fluxos do produto](#fluxos-do-produto)
- [Rotas da aplicacao](#rotas-da-aplicacao)
- [Clientes de API](#clientes-de-api)
- [Dashboards e graficos](#dashboards-e-graficos)
- [Fontes de dados](#fontes-de-dados)
- [Colaboracao e permissoes](#colaboracao-e-permissoes)
- [Autenticacao e sessao](#autenticacao-e-sessao)
- [Como executar](#como-executar)
- [Build e deploy](#build-e-deploy)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Resumo tecnico para recrutadores](#resumo-tecnico-para-recrutadores)

## Visao geral

O `datapilot-frontend` e a camada de produto do DataPilot. Ele organiza uma experiencia completa de SaaS: login, cadastro, perfil, fontes de dados, dashboards gerados por IA, chat, colaboracao, notificacoes, personalizacao visual e exportacao.

O frontend nao tenta substituir as regras de negocio do backend. Ele orquestra a jornada do usuario, renderiza estados, envia comandos para as APIs, trata sessao expirada e apresenta os resultados de forma clara para uso diario.

Responsabilidades principais:

- Proteger areas privadas com token JWT armazenado no navegador.
- Entregar onboarding de cadastro, verificacao por codigo e recuperacao de senha.
- Permitir upload ou conexao de fontes de dados.
- Acionar a API de IA para gerar dashboards com status em tempo real.
- Renderizar graficos interativos com Recharts.
- Permitir customizacao visual dos graficos.
- Exibir analises geradas por IA com React Markdown.
- Exportar dashboards para PDF.
- Criar e manter conversas com o agente de IA.
- Gerenciar convites, acessos compartilhados e permissoes.
- Exibir notificacoes e atualizar estado de leitura.

## Como o SaaS funciona

O DataPilot segue um fluxo de SaaS orientado a workspace individual e colaborativo.

```text
Usuario cria conta
    |
    v
Configura perfil
    |
    v
Cadastra uma fonte de dados
    |
    v
Pede uma analise em linguagem natural
    |
    v
AI Agent gera plano, graficos e analise
    |
    v
Accounts/Data API salva dashboard e configuracoes
    |
    v
Frontend renderiza, customiza, exporta e compartilha
```

### Pilares do produto

| Pilar | Como aparece no frontend |
| --- | --- |
| Aquisicao de usuario | Login, cadastro, validacao de e-mail e recuperacao de senha. |
| Ativacao | Setup de foto, home logada e acoes rapidas para criar fonte, chat ou dashboard. |
| Valor principal | Transformar uma fonte de dados em dashboard e analise executiva com IA. |
| Retencao | Historico de conversas, dashboards recentes, fontes reutilizaveis e atualizacoes automaticas. |
| Colaboracao | Compartilhamento de dashboards com permissao `read`, `edit` ou `full`. |
| Operacao diaria | Notificacoes, busca global, sidebar persistente e exportacao em PDF. |

## Arquitetura

```text
Browser
    |
    v
React + Vite
    |
    +--> src/App.jsx                 -> mapa de rotas
    +--> src/routes/PrivateRoute.jsx -> protecao por token
    |
    +--> src/components/
    |       +--> AppLayout.jsx       -> shell logado, topbar e busca
    |       +--> Sidebar.jsx         -> navegacao, modais globais e notificacoes
    |       +--> Loading.jsx         -> estados de carregamento
    |       +--> ProfileAvatar.jsx   -> identidade do usuario
    |
    +--> src/pages/
    |       +--> Login/Register      -> autenticacao
    |       +--> Home                -> central do workspace
    |       +--> DataSources         -> fontes de dados
    |       +--> Dashboards          -> BI, graficos e IA
    |       +--> Collaborations      -> compartilhamento
    |       +--> Chat                -> conversa com IA
    |       +--> Settings            -> conta e seguranca
    |
    +--> src/api/
            +--> accountsApi.js      -> API de contas/dados
            +--> dataSourceApi.js    -> fontes
            +--> dashboardApi.js     -> dashboards + AI Agent
            +--> collaborationApi.js -> convites e notificacoes
            +--> aiApi.js            -> chat IA
```

### Integracao entre servicos

```text
Frontend
    |
    +--> Accounts/Data API
    |       - usuarios
    |       - autenticacao
    |       - conversas
    |       - fontes de dados
    |       - dashboards
    |       - colaboracoes
    |       - notificacoes
    |
    +--> AI Agent API
            - chat com IA
            - geracao de dashboard
            - streaming de progresso
            - refresh de analise
```

## Tecnologias

| Tecnologia | Uso no projeto |
| --- | --- |
| React 19 | Construcao da interface e composicao de telas. |
| Vite 8 | Ambiente de desenvolvimento, build e preview. |
| React Router DOM 7 | Roteamento SPA e protecao de rotas privadas. |
| Recharts | Renderizacao de barras, linhas, area, pizza, donut, scatter, KPI e tabelas. |
| Lucide React | Icones consistentes para navegacao, acoes e estados. |
| React Hot Toast | Feedback de sucesso, erro e sessao expirada. |
| React Markdown | Renderizacao das analises textuais geradas pela IA. |
| html2canvas | Captura visual do dashboard para exportacao. |
| jsPDF | Geracao de arquivos PDF. |
| ESLint | Verificacao estatica do codigo. |
| serve | Servir o build estatico em producao. |

## Principais funcionalidades

- Autenticacao completa com login, cadastro, codigo por e-mail e recuperacao de senha.
- Area privada protegida por `PrivateRoute`.
- Home com KPIs do workspace, atalhos e itens recentes.
- Sidebar com dashboards, compartilhados, chats, notificacoes e modais globais.
- Busca global na topbar para abrir dashboards e conversas.
- Chat com IA usando historico persistido.
- Cadastro de fontes por arquivo, API externa ou banco PostgreSQL.
- Preview tabular das fontes de dados.
- Atualizacao manual ou agendada de fontes.
- Geracao de dashboard por IA com streaming de status.
- Fallback com polling quando a geracao demora ou a conexao oscila.
- Atualizacao de prompt para reconstruir analises.
- Customizacao de cores, eixos, grade, barras, legenda e fatias de pizza.
- Drill-down em graficos com hierarquia.
- Exportacao de dashboard para PDF.
- Compartilhamento com busca de usuarios e permissoes por nivel.
- Convites recebidos, dashboard compartilhado e remocao de acesso.
- Perfil com nome, username, foto, senha e exclusao de conta.

## Fluxos do produto

### 1. Cadastro e ativacao

```text
Register.jsx
    -> validUser / validUsername
    -> sendCreateCode
    -> saveRegisterData
    -> RegisterCode.jsx
    -> createUser
    -> saveToken
    -> ProfilePhotoSetup.jsx
    -> Home.jsx
```

### 2. Login

```text
Login.jsx
    -> accountsApi.login
    -> saveToken
    -> getMe
    -> Home.jsx ou ProfilePhotoSetup.jsx
```

### 3. Criacao de fonte de dados

```text
DataSources.jsx
    -> usuario escolhe tipo: file, web ou database
    -> monta FormData
    -> dataSourceApi.createDataSource
    -> Accounts/Data API normaliza e salva
    -> frontend mostra preview, linhas e colunas
```

### 4. Geracao de dashboard com IA

```text
Sidebar.jsx ou Dashboards.jsx
    -> usuario escolhe fonte, titulo e prompt
    -> dashboardApi.generateDashboard
    -> AI Agent /dashboard/analyze/stream
    -> frontend recebe status incremental
    -> AI Agent salva dashboard via Accounts/Data API
    -> frontend abre o dashboard criado
```

### 5. Atualizacao de dashboard

```text
Dashboards.jsx
    -> usuario atualiza fonte ou prompt
    -> dashboardApi.refreshDashboard
    -> AI Agent recalcula graficos
    -> Accounts/Data API persiste refresh
    -> frontend recarrega dashboard
```

### 6. Chat com IA

```text
Sidebar.jsx cria conversa
    -> Chat.jsx abre conversa
    -> saveConversationMessage(role=user)
    -> aiApi.sendChatMessage
    -> saveConversationMessage(role=assistant)
    -> renderiza resposta
```

### 7. Colaboracao

```text
Collaborations.jsx
    -> busca usuario por nome ou username
    -> escolhe dashboard e permissao
    -> envia convite
    -> destinatario aceita ou recusa
    -> dashboards compartilhados aparecem na sidebar e home
```

## Rotas da aplicacao

### Rotas publicas

| Rota | Pagina | Funcao |
| --- | --- | --- |
| `/` | `Login.jsx` | Login do usuario. |
| `/register` | `Register.jsx` | Inicio do cadastro. |
| `/register-code` | `RegisterCode.jsx` | Validacao do codigo e criacao da conta. |
| `/forgot-password` | `ForgotPassword.jsx` | Solicita codigo para redefinir senha. |
| `/forgot-password-code` | `ForgotPasswordCode.jsx` | Confirma codigo e salva nova senha. |

### Rotas privadas

Todas passam por `PrivateRoute`, que exige token no `localStorage`.

| Rota | Pagina | Funcao |
| --- | --- | --- |
| `/profile-photo-setup` | `ProfilePhotoSetup.jsx` | Configuracao inicial de foto. |
| `/home` | `Home.jsx` | Central do workspace. |
| `/dashboards` | `Dashboards.jsx` | Lista, abre, gera, customiza, atualiza, exporta e compartilha dashboards. |
| `/data-sources` | `DataSources.jsx` | Cria, visualiza, atualiza e exclui fontes de dados. |
| `/collaborations` | `Collaborations.jsx` | Compartilhamentos, convites e permissoes. |
| `/chat` | `Chat.jsx` | Chat com IA sem conversa especifica aberta. |
| `/chat/:conversationId` | `Chat.jsx` | Chat com historico de conversa. |
| `/movimentacoes` | `Movimentacoes.jsx` | Rota cadastrada em `App.jsx`. |
| `/relatorios` | `Relatorios.jsx` | Area de relatorios. |
| `/sobre-nos` | `About.jsx` | Pagina institucional da equipe. |
| `/help` | `Help.jsx` | Ajuda ao usuario. |
| `/settings` | `Settings.jsx` | Perfil, username, imagem, senha e exclusao de conta. |
| `/settings/recover-password` | `SettingsRecoverPassword.jsx` | Recuperacao/troca de senha logada. |

Rota coringa:

```text
* -> redireciona para /home
```

## Clientes de API

### `src/api/accountsApi.js`

Cliente de autenticacao, perfil e conversas.

Funcoes principais:

- `validUser(email)`
- `validUsername(username)`
- `login(email, password)`
- `sendCreateCode(email)`
- `createUser(userData)`
- `validToken(token)`
- `getMe(token)`
- `updateName(token, name)`
- `updateUsername(token, username)`
- `updateProfileImage(token, profile_image)`
- `updatePassword(token, current_password, password)`
- `sendPasswordCode(email)`
- `sendPasswordCodeByToken(token)`
- `updateAuthPassword(email, code, password)`
- `updateAuthPasswordByToken(token, code, password)`
- `deleteAccount(token, password)`
- `createConversation(token, title)`
- `getConversations(token)`
- `getConversationMessages(token, conversation_id)`
- `saveConversationMessage({ token, conversation_id, role, content })`
- `deleteConversation(token, conversation_id)`

### `src/api/aiApi.js`

Cliente do chat com a API de IA.

```js
sendChatMessage({ token, conversation_id, question })
```

Chama:

```text
POST {AI_URL}/chat
```

### `src/api/dashboardApi.js`

Cliente de dashboards, geracao com IA, refresh, leitura, exclusao e configuracao visual.

Funcoes principais:

- `generateDashboard({ token, title, prompt, data_source_id, onStatus })`
- `refreshDashboard({ token, dashboard, prompt })`
- `refreshDashboards({ token, dashboards })`
- `getDashboards(token)`
- `getDashboard(token, dashboard_id)`
- `deleteDashboard(token, dashboard_id)`
- `saveChartSettings({ ... })`

Detalhe importante: quando `onStatus` existe, `generateDashboard` tenta usar `/dashboard/analyze/stream`. Se a conexao cair, mas o backend tiver criado o dashboard, o frontend faz polling em `/dashboards` para recuperar o resultado.

### `src/api/dataSourceApi.js`

Cliente de fontes de dados.

Funcoes principais:

- `createDataSource({ token, name, sourceType, file, apiUrl, apiPayload, databaseUrl, query, refreshIntervalDays })`
- `getDataSources(token)`
- `getDataSource(token, data_source_id)`
- `getLinkedDashboards(token, data_source_id)`
- `updateDataSource({ ... })`
- `renameDataSource({ token, data_source_id, name })`
- `deleteDataSource(token, data_source_id)`

### `src/api/collaborationApi.js`

Cliente de colaboracao, convites, acessos e notificacoes.

Funcoes principais:

- `getCollaborationOverview(token)`
- `searchUsers(token, query)`
- `getDashboardCollaborators(token, dashboard_id)`
- `shareDashboard({ token, dashboard_id, username, permission })`
- `updateCollaboration({ token, collaboration_id, permission })`
- `deleteCollaboration(token, collaboration_id)`
- `respondInvitation(token, collaboration_id, response)`
- `getDashboardAccess(token, dashboard_id)`
- `getNotifications(token)`
- `markNotificationRead(token, notification_id)`

## Dashboards e graficos

Os dashboards sao renderizados com Recharts e recebem dados ja calculados pelo backend. A pagina `Dashboards.jsx` centraliza visualizacao, configuracao, refresh, exportacao e controle de acesso.

Tipos suportados na interface:

| Tipo | Uso |
| --- | --- |
| Barras | Comparacao por categorias. |
| Barras horizontais | Rankings e categorias com nomes longos. |
| Linha | Evolucao temporal. |
| Area | Tendencia visual e volume ao longo do tempo. |
| Pizza | Participacao percentual. |
| Donut | Participacao percentual em anel. |
| Dispersao | Relacao entre metricas numericas. |
| KPI | Indicador unico. |
| Tabela | Detalhamento tabular. |

Configuracoes visuais persistidas:

- cor principal do grafico;
- cor de fundo;
- cor dos eixos X e Y;
- cor da grade;
- estilo da grade;
- estilo das barras;
- cores individuais de fatias;
- exibicao de legenda.

Exportacao:

```text
Dashboards.jsx
    -> html2canvas captura #dashboard-export-area
    -> jsPDF gera PDF em landscape
    -> navegador baixa o arquivo
```

## Fontes de dados

A pagina `DataSources.jsx` permite cadastrar e atualizar dados que serao usados nos dashboards.

Tipos suportados:

| Tipo | Entrada | Uso |
| --- | --- | --- |
| `file` | CSV, XLS, XLSX ou JSON | Upload direto de arquivo. |
| `web` | URL de API externa | Buscar dados de um endpoint HTTP. |
| `database` | PostgreSQL + query SELECT | Consultar dados de banco relacional. |

Recursos da area:

- preview de linhas e colunas;
- contagem de linhas e colunas;
- update manual de fonte;
- intervalo de atualizacao em dias;
- deteccao de dashboards vinculados;
- opcao de atualizar so a fonte ou fonte + dashboards;
- protecao visual contra excluir fonte compartilhada.

## Colaboracao e permissoes

O SaaS permite que um dashboard seja compartilhado com outros usuarios.

Permissoes:

| Permissao | Impacto na interface |
| --- | --- |
| `read` | Usuario visualiza o dashboard, mas nao edita configuracoes nem atualiza analise. |
| `edit` | Usuario pode ajustar configuracoes visuais permitidas. |
| `full` | Usuario pode atualizar a analise e trabalhar com acesso mais amplo. |

Fluxos:

- buscar usuarios por nome ou username;
- enviar convite;
- aceitar ou recusar convite;
- listar pessoas com acesso;
- alterar permissao;
- remover colaborador;
- remover o proprio acesso a um dashboard compartilhado;
- mostrar dashboards compartilhados na home e sidebar.

## Autenticacao e sessao

O token JWT fica salvo em `localStorage` por `src/utils/storage.js`.

Funcoes principais:

| Funcao | Responsabilidade |
| --- | --- |
| `saveToken(token)` | Salva o JWT depois do login/cadastro. |
| `getToken()` | Recupera o JWT usado pelos clientes de API. |
| `removeToken()` | Remove o JWT. |
| `logout()` | Limpa token, dados temporarios de cadastro e e-mail de reset. |
| `saveRegisterData(data)` | Guarda dados temporarios entre cadastro e validacao de codigo. |
| `saveResetEmail(email)` | Guarda e-mail durante recuperacao de senha. |

Sessao expirada:

```text
API retorna 401 ou mensagem de token invalido
    -> isSessionExpiredError detecta
    -> handleExpiredSession limpa storage
    -> toast informa o usuario
    -> redirect para /
```

## URLs das APIs

As URLs estao definidas diretamente nos clientes em `src/api/`.

| API | URL atual | Arquivos |
| --- | --- | --- |
| Accounts/Data API | `https://web-production-81b91.up.railway.app` | `accountsApi.js`, `dashboardApi.js`, `dataSourceApi.js`, `collaborationApi.js` |
| AI Agent API | `https://web-production-40ead.up.railway.app` | `aiApi.js`, `dashboardApi.js` |

Melhoria recomendada:

```env
VITE_ACCOUNTS_URL=https://...
VITE_AI_URL=https://...
```

Assim cada ambiente pode trocar backend sem alterar codigo fonte.

## Como executar

### Requisitos

- Node.js compativel com Vite.
- npm.
- APIs de backend acessiveis pelas URLs configuradas.

### Instalar dependencias

```bash
npm install
```

### Desenvolvimento

```bash
npm run dev
```

URL padrao:

```text
http://localhost:5173
```

### Lint

```bash
npm run lint
```

### Preview local do build

```bash
npm run build
npm run preview
```

## Build e deploy

Build de producao:

```bash
npm run build
```

Servir build estatico:

```bash
npm run start
```

O script de producao usa:

```text
serve -s dist -l $PORT
```

Esse formato funciona bem em plataformas que injetam `PORT`, como Railway, Render e ambientes similares.

## Estrutura de pastas

```text
datapilot-frontend/
|-- public/
|   |-- team/
|   |-- black_logo.png
|   |-- datapilot-logo-dark.svg
|   |-- datapilot-logo-light.svg
|   |-- favicon.svg
|   `-- logo.jpeg
|-- src/
|   |-- api/
|   |   |-- accountsApi.js
|   |   |-- aiApi.js
|   |   |-- collaborationApi.js
|   |   |-- dashboardApi.js
|   |   `-- dataSourceApi.js
|   |-- components/
|   |-- pages/
|   |-- routes/
|   |-- styles/
|   |-- utils/
|   |-- App.jsx
|   `-- main.jsx
|-- index.html
|-- package.json
|-- vite.config.js
|-- eslint.config.js
`-- README.md
```

## Observacoes de manutencao

- `src/App.jsx` ainda importa `src/pages/Movimentacoes.jsx` para a rota `/movimentacoes`.
- Se essa pagina for removida de vez, remova tambem o import e a rota correspondente.
- As URLs das APIs estao hardcoded e devem ser migradas para variaveis `VITE_*`.
- O frontend valida experiencia e navegacao, mas permissao final precisa continuar no backend.
- O fluxo de dashboard depende da API de IA e da API de contas; em caso de indisponibilidade parcial, o frontend tenta recuperar o dashboard criado com polling.

## Resumo tecnico para recrutadores

Este frontend demonstra uma aplicacao SaaS completa, nao apenas uma colecao de telas. Ele cobre onboarding, autenticacao, estado privado, integracao com microservicos, upload e conexao de dados, geracao de dashboards por IA, visualizacao interativa, colaboracao, notificacoes, exportacao e configuracao de conta.

O ponto mais forte da arquitetura e a orquestracao entre experiencia do usuario e backends especializados. A interface lida com estados reais de produto: criacao assincrona de dashboards, streaming, fallback por polling, permissoes de colaboracao, sessao expirada, fontes compartilhadas, atualizacao de dados e renderizacao de analises geradas por IA.
