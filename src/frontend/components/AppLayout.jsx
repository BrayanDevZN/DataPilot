import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Search,
  Plus,
  BarChart3,
  Bell,
  MessageSquareText,
} from "lucide-react";

import Sidebar from "./Sidebar";
import { getToken } from "../utils/storage";
import { getConversations } from "../api/accountsApi";
import { getDashboards } from "../api/dashboardApi";

const PAGE_TITLES = {
  home: "Início",
  dashboards: "Dashboards",
  chat: "IA Financeira",
  settings: "Configurações",
  dataSources: "Fontes de Dados",
  collaborations: "Colaborações",
  help: "Ajuda",
};

function getPageInfo(pathname) {
  if (pathname.startsWith("/home")) {
    return {
      key: "home",
      title: PAGE_TITLES.home,
      subtitle: "Central da plataforma.",
    };
  }

  if (pathname.startsWith("/dashboards")) {
    return {
      key: "dashboards",
      title: PAGE_TITLES.dashboards,
      subtitle: "Visualize dashboards, gráficos e análises geradas.",
    };
  }

  if (pathname.startsWith("/data-sources")) {
    return {
      key: "dataSources",
      title: PAGE_TITLES.dataSources,
      subtitle: "Gerencie planilhas e fontes usadas nas análises.",
    };
  }

  if (pathname.startsWith("/collaborations")) {
    return {
      key: "collaborations",
      title: PAGE_TITLES.collaborations,
      subtitle: "Compartilhe dashboards e controle o acesso da sua equipe.",
    };
  }

  if (pathname.startsWith("/chat")) {
    return {
      key: "chat",
      title: PAGE_TITLES.chat,
      subtitle: "Converse com a IA e transforme dados em decisões.",
    };
  }

  if (pathname.startsWith("/settings")) {
    return {
      key: "settings",
      title: PAGE_TITLES.settings,
      subtitle: "Gerencie seu perfil e preferências de acesso.",
    };
  }

  if (pathname.startsWith("/help")) {
    return {
      key: "help",
      title: PAGE_TITLES.help,
      subtitle: "Encontre ajuda para usar a plataforma.",
    };
  }

  return {
    key: "home",
    title: PAGE_TITLES.home,
    subtitle: "Central da plataforma.",
  };
}

export default function AppLayout({
  children,
  hideTopbar = false,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const page = getPageInfo(location.pathname);

  const [search, setSearch] = useState("");
  const [dashboards, setDashboards] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState(0);

  async function loadSearchData() {
    try {
      const token = getToken();

      if (!token) return;

      const [dashboardsResponse, conversationsResponse] =
        await Promise.all([
          getDashboards(token),
          getConversations(token),
        ]);

      setDashboards(dashboardsResponse?.dashboards || []);

      const chats = Array.isArray(conversationsResponse)
        ? conversationsResponse
        : conversationsResponse?.conversations || [];

      setConversations(chats);
    } catch (err) {
      console.error("Erro ao carregar pesquisa:", err);
      setDashboards([]);
      setConversations([]);
    }
  }

  useEffect(() => {
    if (!hideTopbar) {
      loadSearchData();
    }
  }, [location.pathname, hideTopbar]);

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

  const searchResults = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) {
      return {
        dashboards: [],
        chats: [],
      };
    }

    return {
      dashboards: dashboards
        .filter((dashboard) =>
          dashboard.title?.toLowerCase().includes(term)
        )
        .slice(0, 5),

      chats: conversations
        .filter((chat) =>
          chat.title?.toLowerCase().includes(term)
        )
        .slice(0, 5),
    };
  }, [search, dashboards, conversations]);

  function closeSearch() {
    setSearch("");
    setShowSuggestions(false);
  }

  function openDashboard(id) {
    closeSearch();
    navigate(`/dashboards?dashboard_id=${id}`);
  }

  function openChat(chat) {
    const id = chat.conversation_id || chat.id;
    const title = chat.title || `Conversa #${id}`;

    closeSearch();

    navigate(`/chat/${id}`, {
      state: { title },
    });
  }

  const hasResults =
    searchResults.dashboards.length > 0 ||
    searchResults.chats.length > 0;

  return (
    <main className="app-layout">
      <Sidebar />

      <section className="app-shell">
        {!hideTopbar && (
          <header className="topbar">
            <div className="topbar-title">
              <span className="topbar-eyebrow">
                DataPilot AI
              </span>

              <h1>{page.title}</h1>

              <p>{page.subtitle}</p>
            </div>

            <div className="topbar-actions">
              <div className="topbar-search-wrapper">
                <label
                  className="topbar-search"
                  aria-label="Pesquisar"
                >
                  <Search size={18} />

                  <input
                    value={search}
                    placeholder="Pesquisar dashboards e chats..."
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() =>
                      setShowSuggestions(true)
                    }
                  />
                </label>

                {showSuggestions && search.trim() && (
                  <div className="topbar-search-suggestions">
                    {hasResults ? (
                      <>
                        {searchResults.dashboards.length > 0 && (
                          <div className="search-group">
                            <span className="search-group-title">
                              Dashboards
                            </span>

                            {searchResults.dashboards.map(
                              (dashboard) => (
                                <button
                                  key={dashboard.id}
                                  type="button"
                                  onMouseDown={(event) =>
                                    event.preventDefault()
                                  }
                                  onClick={() =>
                                    openDashboard(dashboard.id)
                                  }
                                >
                                  <BarChart3 size={17} />

                                  <div>
                                    <strong>
                                      {dashboard.title}
                                    </strong>

                                    <span>
                                      Abrir dashboard
                                    </span>
                                  </div>
                                </button>
                              )
                            )}
                          </div>
                        )}

                        {searchResults.chats.length > 0 && (
                          <div className="search-group">
                            <span className="search-group-title">
                              Chats
                            </span>

                            {searchResults.chats.map((chat) => {
                              const id =
                                chat.conversation_id ||
                                chat.id;

                              const title =
                                chat.title ||
                                `Conversa #${id}`;

                              return (
                                <button
                                  key={id}
                                  type="button"
                                  onMouseDown={(event) =>
                                    event.preventDefault()
                                  }
                                  onClick={() =>
                                    openChat(chat)
                                  }
                                >
                                  <MessageSquareText size={17} />

                                  <div>
                                    <strong>
                                      {title}
                                    </strong>

                                    <span>
                                      Abrir conversa
                                    </span>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="search-empty">
                        Nenhum resultado encontrado.
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="topbar-cta-group">
                <button
                  type="button"
                  className="topbar-notification-button"
                  onClick={() =>
                    window.dispatchEvent(
                      new Event("open-notifications-modal")
                    )
                  }
                  title="Notificações"
                  aria-label="Abrir notificações"
                >
                  <Bell size={22} strokeWidth={2.4} />
                  {unreadNotifications > 0 && (
                    <span>{unreadNotifications}</span>
                  )}
                </button>

                <button
                  type="button"
                  className="topbar-cta topbar-cta-secondary"
                  onClick={() =>
                    window.dispatchEvent(
                      new Event("open-chat-modal")
                    )
                  }
                >
                  <MessageSquareText size={18} />
                  <span>Novo chat</span>
                  <Plus size={16} />
                </button>

                <button
                  type="button"
                  className="topbar-cta"
                  onClick={() =>
                    window.dispatchEvent(
                      new Event(
                        "open-dashboard-modal"
                      )
                    )
                  }
                >
                  <BarChart3 size={18} />
                  <span>Novo dashboard</span>
                  <Plus size={16} />
                </button>
              </div>
            </div>
          </header>
        )}

        <section
          className={
            hideTopbar
              ? "app-content app-content-full"
              : "app-content"
          }
        >
          {children}
        </section>
      </section>
    </main>
  );
}
