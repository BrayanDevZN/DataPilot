import {
  AlertTriangle,
  BarChart3,
  Bell,
  Bot,
  CheckCircle2,
  CircleHelp,
  Database,
  FileDown,
  FileSpreadsheet,
  Globe2,
  Lightbulb,
  Link,
  MessageCircle,
  Palette,
  RefreshCcw,
  Server,
  Share2,
  Sparkles,
  Upload,
} from "lucide-react";

import AppLayout from "../components/AppLayout";

const QUICK_STEPS = [
  "Cadastre uma fonte de dados.",
  "Crie um dashboard com um objetivo claro.",
  "Revise os graficos e a analise da IA.",
  "Compartilhe, exporte ou atualize quando os dados mudarem.",
];

const HELP_SECTIONS = [
  {
    icon: Database,
    title: "Fontes de dados",
    text: "A fonte e o conjunto de dados que alimenta dashboards e analises. Ela pode vir de arquivo, API externa ou banco de dados.",
    bullets: [
      "Arquivo: CSV, XLSX, XLS ou JSON.",
      "Web: o backend consulta a URL da API, salva a URL, salva os dados e respeita o intervalo de atualizacao.",
      "Banco de dados: informe host, porta, usuario, senha, banco e uma consulta SELECT.",
    ],
  },
  {
    icon: Globe2,
    title: "APIs externas",
    text: "Ao salvar uma API, o DataPilot faz a requisicao no backend e grava o resultado em banco. Quando o prazo configurado vencer, a API sera consultada de novo.",
    bullets: [
      "Use uma URL acessivel pelo backend publicado.",
      "URLs localhost so funcionam se o backend do DataPilot tambem estiver rodando na sua maquina.",
      "A resposta deve ser JSON: lista direta ou objeto com chaves como data, results, items, rows, products ou users.",
    ],
  },
  {
    icon: Server,
    title: "Bancos de dados",
    text: "A conexao por banco busca dados com uma consulta SELECT e salva o resultado como fonte reutilizavel.",
    bullets: [
      "Use somente SELECT para evitar alteracoes acidentais.",
      "Prefira consultas com limite de linhas quando a tabela for grande.",
      "Revise credenciais e permissao de rede antes de salvar.",
    ],
  },
  {
    icon: BarChart3,
    title: "Dashboards",
    text: "Dashboards transformam uma fonte em graficos e analise textual. Cada dashboard fica ligado a uma fonte para poder ser atualizado depois.",
    bullets: [
      "Escolha uma fonte cadastrada.",
      "Escreva o que voce quer descobrir.",
      "A IA monta graficos, metricas e uma leitura dos principais sinais.",
    ],
  },
  {
    icon: RefreshCcw,
    title: "Atualizacao automatica",
    text: "Fontes com intervalo de dias sao verificadas quando o usuario entra. Se o prazo venceu, o backend atualiza a fonte e refaz os dashboards ligados.",
    bullets: [
      "Os dados novos substituem os antigos no banco.",
      "Os dashboards ligados sao recriados com o prompt salvo.",
      "Uma notificacao informa se a atualizacao automatica terminou ou se precisa de acao manual.",
    ],
  },
  {
    icon: Bot,
    title: "IA e prompts",
    text: "A IA interpreta seu pedido, escolhe operacoes, gera graficos e escreve uma analise com base nos dados disponiveis.",
    bullets: [
      "Seja especifico sobre objetivo, periodo, categorias e metricas.",
      "Evite pedidos vagos como 'analise isso'.",
      "Revise os resultados antes de usar em decisoes importantes.",
    ],
  },
  {
    icon: Share2,
    title: "Colaboracoes",
    text: "Voce pode compartilhar dashboards com outras pessoas e controlar permissoes de leitura, edicao ou acesso completo.",
    bullets: [
      "Convites aparecem na area de notificacoes.",
      "Dashboards compartilhados ficam separados dos seus dashboards.",
      "Acesso completo tambem permite usar a fonte ligada ao dashboard.",
    ],
  },
  {
    icon: Bell,
    title: "Notificacoes",
    text: "O sino mostra convites, respostas de colaboracao e eventos automaticos, como dashboards refeitos apos atualizacao de fonte.",
    bullets: [
      "Notificacoes nao lidas aparecem no contador.",
      "Ao abrir o painel, elas sao marcadas como lidas.",
      "Quando houver dashboard ligado, o clique leva para a area relacionada.",
    ],
  },
  {
    icon: Palette,
    title: "Ajustes visuais",
    text: "Os graficos podem receber cores, fundo, textos de eixo, grade, estilo de barras e paleta de pizza.",
    bullets: [
      "Salve as configuracoes para manter o visual ao reabrir.",
      "Use cores com contraste para apresentacoes.",
      "Evite excesso de estilos quando o objetivo for comparar dados rapidamente.",
    ],
  },
  {
    icon: FileDown,
    title: "Exportacao",
    text: "A exportacao gera um PDF com graficos e analise da IA, pronto para relatorios, trabalhos ou reunioes.",
    bullets: [
      "Confira o dashboard antes de exportar.",
      "Use titulos claros nos graficos.",
      "Atualize a fonte antes de gerar relatorios recorrentes.",
    ],
  },
  {
    icon: MessageCircle,
    title: "Chats da IA",
    text: "O chat serve para tirar duvidas, pedir explicacoes, discutir ideias e entender conceitos sobre dados.",
    bullets: [
      "Use o chat para perguntas abertas.",
      "Use dashboards para analise visual estruturada.",
      "Conversas recentes ficam no menu lateral.",
    ],
  },
  {
    icon: AlertTriangle,
    title: "Limites e cuidados",
    text: "O DataPilot ajuda muito, mas a qualidade da analise depende da qualidade da fonte.",
    bullets: [
      "Colunas mal nomeadas reduzem a precisao.",
      "Dados incompletos podem distorcer graficos.",
      "Resultados da IA devem ser revisados antes de decisoes criticas.",
    ],
    warning: true,
  },
];

export default function Help() {
  return (
    <AppLayout>
      <main className="help-page">
        <section className="help-hero">
          <div className="help-hero-copy">
            <span className="help-kicker">
              <CircleHelp size={18} />
              Central de ajuda
            </span>
            <h1>Guia completo do DataPilot AI</h1>
            <p>
              Entenda como cadastrar dados, criar dashboards com IA, manter
              fontes atualizadas, colaborar com outras pessoas e transformar
              informacao bruta em decisoes mais claras.
            </p>
          </div>

          <div className="help-hero-panel">
            <Sparkles size={24} />
            <strong>Fluxo recomendado</strong>
            <ol>
              {QUICK_STEPS.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        </section>

        <section className="help-flow">
          <article>
            <FileSpreadsheet size={22} />
            <strong>1. Dados</strong>
            <span>Arquivo, API ou banco.</span>
          </article>
          <article>
            <Upload size={22} />
            <strong>2. Fonte</strong>
            <span>Dados salvos e reutilizaveis.</span>
          </article>
          <article>
            <BarChart3 size={22} />
            <strong>3. Dashboard</strong>
            <span>Graficos e analise por IA.</span>
          </article>
          <article>
            <RefreshCcw size={22} />
            <strong>4. Atualizacao</strong>
            <span>Fonte e dashboards refeitos.</span>
          </article>
        </section>

        <section className="help-detail-panel">
          <div>
            <span className="help-kicker">
              <Lightbulb size={18} />
              Exemplo de bom pedido
            </span>
            <p>
              "Compare as categorias com maior receita, destaque produtos com
              melhor margem e mostre oportunidades de estoque para o proximo
              mes."
            </p>
          </div>
          <div>
            <span className="help-kicker">
              <Link size={18} />
              Regra de ouro
            </span>
            <p>
              Quanto mais claro for o objetivo, melhor a IA consegue escolher
              metricas, agrupamentos e graficos relevantes.
            </p>
          </div>
        </section>

        <section className="help-grid">
          {HELP_SECTIONS.map((section) => {
            const Icon = section.icon;

            return (
              <article
                key={section.title}
                className={`help-card ${section.warning ? "help-warning" : ""}`}
              >
                <div className="help-card-icon">
                  <Icon size={24} />
                </div>
                <h2>{section.title}</h2>
                <p>{section.text}</p>
                <ul>
                  {section.bullets.map((item) => (
                    <li key={item}>
                      <CheckCircle2 size={16} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </article>
            );
          })}
        </section>
      </main>
    </AppLayout>
  );
}
