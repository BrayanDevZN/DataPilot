# DataPilot AI - Frontend adaptado

Este pacote usa o projeto do primeiro ZIP como base e aplica o visual do DataPilot AI sem alterar a estrutura essencial de integração.

## Mantido do primeiro projeto

- Rotas principais: login, cadastro, recuperação de senha, dashboards, chat e configurações.
- Integração com as APIs em `src/api/*`.
- Fluxo de autenticação via token/localStorage.
- Criação, listagem e exclusão de chats.
- Criação, listagem, edição visual, exportação e exclusão de dashboards.
- Estrutura React/Vite em JavaScript.

## Adaptado do DataPilot

- Sidebar escura com identidade DataPilot AI.
- Logo DataPilot em SVG no `public/`.
- Header superior com busca, notificação visual e CTA.
- Cards, modais, inputs, botões e layout com estética azul escura.
- Login com aparência mais próxima do DataPilot financeiro.
- Chat e dashboards reestilizados sem mexer nas chamadas da API.

## Rodar localmente

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

O build foi testado com sucesso neste pacote.
