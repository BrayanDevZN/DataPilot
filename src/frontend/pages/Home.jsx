import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  Database,
  MessageSquare,
  Plus,
  RefreshCcw,
  Settings,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  Bell,
} from "lucide-react";

import AppLayout from "../components/AppLayout";
import Loading from "../components/Loading";
import ProfileAvatar from "../components/ProfileAvatar";
import { getDashboards } from "../api/dashboardApi";
import { getDataSources } from "../api/dataSourceApi";
import { getConversations, getMe } from "../api/accountsApi";
import { getToken } from "../utils/storage";

function getConversationId(conversation) {
  return conversation.conversation_id || conversation.id;
}

function getUserName(meResponse) {
  return (
    meResponse?.name ||
    meResponse?.user?.name ||
    meResponse?.data?.name ||
    "Usuário"
  );
}

function getUser(meResponse) {
  return meResponse?.user || meResponse?.data || meResponse || {};
}

export default function Home() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [dashboards, setDashboards] = useState([]);
  const [sharedDashboards, setSharedDashboards] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState(0);

  async function loadHomeData() {
    try {
      setLoading(true);

      const token = getToken();

      const [
        meResponse,
        dashboardsResponse,
        dataSourcesResponse,
        conversationsResponse,
      ] = await Promise.all([
        getMe(token),
        getDashboards(token),
        getDataSources(token),
        getConversations(token),
      ]);

      const chats = Array.isArray(conversationsResponse)
        ? conversationsResponse
        : conversationsResponse?.conversations || [];

      setUser(meResponse);
      setDashboards(dashboardsResponse?.dashboards || []);
      setSharedDashboards(dashboardsResponse?.shared_dashboards || []);
      setDataSources(dataSourcesResponse?.data_sources || []);
      setConversations(chats);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHomeData();
  }, []);

  useEffect(() => {
    function handleNotificationsLoaded(event) {
      setUnreadNotifications(event.detail?.unreadCount || 0);
    }

    window.addEventListener("notifications-loaded", handleNotificationsLoaded);

    return () => {
      window.removeEventListener(
        "notifications-loaded",
        handleNotificationsLoaded
      );
    };
  }, []);

  const userName = getUserName(user);
  const currentUser = getUser(user);

  const outdatedDashboards = useMemo(
    () => dashboards.filter((dashboard) => dashboard.is_outdated),
    [dashboards]
  );

  const recentDashboards = dashboards.slice(0, 4);
  const recentSharedDashboards = sharedDashboards.slice(0, 4);
  const recentSources = dataSources.slice(0, 4);
  const recentChats = conversations.slice(0, 4);

  function openNewChat() {
    window.dispatchEvent(new Event("open-chat-modal"));
  }

  function openNewDashboard() {
    window.dispatchEvent(new Event("open-dashboard-modal"));
  }

  return (
    <AppLayout hideTopbar>
      <main className="home-hub-page">
        <section className="home-hero">
          <div>
            <span className="home-eyebrow">
              <Sparkles size={18} />
              DataPilot AI
            </span>

            <h1>Central da plataforma</h1>

            <p>Fontes, dashboards, análises e conversas organizados em um só lugar.</p>
          </div>

          <div className="home-hero-actions">
            <button
              type="button"
              className="home-notification-button"
              onClick={() =>
                window.dispatchEvent(new Event("open-notifications-modal"))
              }
              title="Notificações"
              aria-label="Abrir notificações"
            >
              <Bell size={22} strokeWidth={2.4} />
              {unreadNotifications > 0 && <span>{unreadNotifications}</span>}
            </button>

            <button onClick={() => navigate("/data-sources")}>
              <Database size={18} />
              Nova fonte
            </button>

            <button onClick={openNewChat}>
              <MessageSquare size={18} />
              Novo chat
            </button>

            <button onClick={openNewDashboard}>
              <Plus size={18} />
              Novo dashboard
            </button>
          </div>
        </section>

        <section className="home-welcome-card">
          <ProfileAvatar
            image={currentUser.profile_image}
            name={userName}
            size="large"
          />

          <div>
            <span>Seu espaço de trabalho</span>
            <h2>Bem-vindo, {userName}</h2>
            <p>
              @{currentUser.username || "usuario"} · Continue de onde parou e
              transforme seus dados em decisões mais claras.
            </p>
          </div>
        </section>

        {loading && (
          <Loading
            compact
            label="Atualizando sua central"
            description="Sincronizando dashboards, fontes e conversas."
          />
        )}

        <section className="home-kpi-grid">
          <button className="home-kpi-card" onClick={() => navigate("/dashboards")}>
            <span className="home-kpi-icon blue">
              <BarChart3 size={24} />
            </span>
            <small>Dashboards</small>
            <strong className={loading ? "is-loading-value" : ""}>
              {loading ? "" : dashboards.length}
            </strong>
          </button>

          <button className="home-kpi-card" onClick={() => navigate("/data-sources")}>
            <span className="home-kpi-icon green">
              <Database size={24} />
            </span>
            <small>Fontes de dados</small>
            <strong className={loading ? "is-loading-value" : ""}>
              {loading ? "" : dataSources.length}
            </strong>
          </button>

          <button className="home-kpi-card" onClick={() => navigate("/chat")}>
            <span className="home-kpi-icon purple">
              <MessageSquare size={24} />
            </span>
            <small>Conversas IA</small>
            <strong className={loading ? "is-loading-value" : ""}>
              {loading ? "" : conversations.length}
            </strong>
          </button>

          <button className="home-kpi-card" onClick={() => navigate("/dashboards")}>
            <span className="home-kpi-icon orange">
              <AlertTriangle size={24} />
            </span>
            <small>Atualizações pendentes</small>
            <strong className={loading ? "is-loading-value" : ""}>
              {loading ? "" : outdatedDashboards.length}
            </strong>
          </button>
        </section>

        <section className="home-main-grid">
          <div className="home-panel">
            <div className="home-panel-header">
              <div>
                <h2>Ações rápidas</h2>
                <p>Comece pelos caminhos mais usados.</p>
              </div>
            </div>

            <div className="home-actions-grid">
              <button className="home-card-button" onClick={() => navigate("/data-sources")}>
                <Database size={22} />
                <span>
                  <strong>Adicionar fonte</strong>
                  <small>Envie CSV, XLSX ou JSON.</small>
                </span>
                <ArrowRight size={18} />
              </button>

              <button className="home-card-button" onClick={openNewDashboard}>
                <BarChart3 size={22} />
                <span>
                  <strong>Criar dashboard</strong>
                  <small>Gere gráficos e análise IA.</small>
                </span>
                <ArrowRight size={18} />
              </button>

              <button className="home-card-button" onClick={openNewChat}>
                <MessageSquare size={22} />
                <span>
                  <strong>Novo chat</strong>
                  <small>Converse com o agente.</small>
                </span>
                <ArrowRight size={18} />
              </button>

              <button className="home-card-button" onClick={() => navigate("/settings")}>
                <Settings size={22} />
                <span>
                  <strong>Configurações</strong>
                  <small>Conta, senha e preferências.</small>
                </span>
                <ArrowRight size={18} />
              </button>
            </div>
          </div>

          <div className="home-panel home-summary-panel">
            <div className="home-panel-header">
              <div>
                <h2>Resumo</h2>
                <p>O estado atual da sua conta.</p>
              </div>

              <RefreshCcw size={18} />
            </div>

            <ul className="home-summary-list">
              <li><span>{dataSources.length}</span> fontes cadastradas.</li>
              <li><span>{dashboards.length}</span> dashboards criados.</li>
              <li><span>{conversations.length}</span> conversas criadas.</li>
              <li><span>{outdatedDashboards.length}</span> dashboards pendentes.</li>
              <li>
                Última fonte:{" "}
                <strong>{recentSources[0]?.name || "nenhuma fonte ainda"}</strong>
              </li>
            </ul>
          </div>
        </section>

        <section className="home-main-grid">
          <div className="home-panel">
            <div className="home-panel-header">
              <div>
                <h2>Dashboards recentes</h2>
                <p>Acesse rapidamente suas análises.</p>
              </div>
            </div>

            <div className="home-recent-list">
              {recentDashboards.length === 0 ? (
                <p className="home-empty">Nenhum dashboard criado ainda.</p>
              ) : (
                recentDashboards.map((dashboard) => (
                  <button
                    className="home-card-button"
                    key={dashboard.id}
                    onClick={() =>
                      navigate(`/dashboards?dashboard_id=${dashboard.id}`)
                    }
                  >
                    <span className="home-recent-icon">
                      <BarChart3 size={18} />
                    </span>

                    <span>
                      <strong>{dashboard.title}</strong>
                      <small>
                        {dashboard.is_outdated ? "Precisa atualizar" : "Atualizado"}
                      </small>
                    </span>

                    <ArrowRight size={18} />
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="home-panel">
            <div className="home-panel-header">
              <div>
                <h2>Chats recentes</h2>
                <p>Continue conversas anteriores.</p>
              </div>
            </div>

            <div className="home-recent-list">
              {recentChats.length === 0 ? (
                <p className="home-empty">Nenhum chat criado ainda.</p>
              ) : (
                recentChats.map((chat) => {
                  const id = getConversationId(chat);
                  const title = chat.title || `Conversa #${id}`;

                  return (
                    <button
                      className="home-card-button"
                      key={id}
                      onClick={() =>
                        navigate(`/chat/${id}`, { state: { title } })
                      }
                    >
                      <span className="home-recent-icon">
                        <MessageSquare size={18} />
                      </span>

                      <span>
                        <strong>{title}</strong>
                        <small>{chat.total_messages || 0} mensagens</small>
                      </span>

                      <ArrowRight size={18} />
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </section>

        <section className="home-panel">
          <div className="home-panel-header">
            <div>
              <h2>Fontes recentes</h2>
              <p>Dados disponíveis para análise.</p>
            </div>
          </div>

          <div className="home-recent-list">
            {recentSources.length === 0 ? (
              <p className="home-empty">Nenhuma fonte cadastrada ainda.</p>
            ) : (
              recentSources.map((source) => (
                <button className="home-card-button" key={source.id} onClick={() => navigate("/data-sources")}>
                  <span className="home-recent-icon">
                    <Database size={18} />
                  </span>

                  <span>
                    <strong>{source.name}</strong>
                    <small>
                      {source.row_count || 0} linhas • {source.column_count || 0} colunas
                    </small>
                  </span>

                  <ArrowRight size={18} />
                </button>
              ))
            )}
          </div>
        </section>

        <section className="home-panel">
          <div className="home-panel-header">
            <div>
              <h2>Compartilhados comigo</h2>
              <p>Dashboards enviados pela sua equipe.</p>
            </div>
          </div>

          <div className="home-recent-list">
            {recentSharedDashboards.length === 0 ? (
              <p className="home-empty">Nenhum dashboard compartilhado com você ainda.</p>
            ) : (
              recentSharedDashboards.map((dashboard) => (
                <button className="home-card-button" key={dashboard.id} onClick={() => navigate(`/dashboards?dashboard_id=${dashboard.id}`)}>
                  <span className="home-recent-icon"><BarChart3 size={18} /></span>
                  <span>
                    <strong>{dashboard.title}</strong>
                    <small>Criado por @{dashboard.creator_username}</small>
                  </span>
                  <ArrowRight size={18} />
                </button>
              ))
            )}
          </div>
        </section>
      </main>
    </AppLayout>
  );
}
