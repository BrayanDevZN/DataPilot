import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Check, Search, Share2, Trash2, UsersRound, X } from "lucide-react";

import AppLayout from "../components/AppLayout";
import Loading from "../components/Loading";
import ProfileAvatar from "../components/ProfileAvatar";
import {
  deleteCollaboration,
  getCollaborationOverview,
  getDashboardCollaborators,
  searchUsers,
  shareDashboard,
  updateCollaboration,
  respondInvitation,
} from "../api/collaborationApi";
import { getToken } from "../utils/storage";

const PERMISSIONS = [
  {
    value: "read",
    label: "Somente leitura",
    description: "Pode visualizar o dashboard.",
  },
  {
    value: "edit",
    label: "Pode editar",
    description: "Tambem pode ajustar a aparencia dos graficos.",
  },
  {
    value: "full",
    label: "Acesso geral",
    description: "Pode atualizar a analise e editar a fonte de dados.",
  },
];

export default function Collaborations() {
  const [dashboards, setDashboards] = useState([]);
  const [sharedDashboards, setSharedDashboards] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [selectedDashboardId, setSelectedDashboardId] = useState("");
  const [collaborators, setCollaborators] = useState([]);
  const [query, setQuery] = useState("");
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchingUsers, setSearchingUsers] = useState(false);
  const [permission, setPermission] = useState("read");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  function notifyCollaborationChange() {
    window.dispatchEvent(new Event("collaborations-updated"));
  }

  async function loadOverview() {
    const response = await getCollaborationOverview(getToken());
    const owned = response?.dashboards || [];
    const requestedDashboardId = new URLSearchParams(
      window.location.search
    ).get("dashboard_id");

    setDashboards(owned);
    setSharedDashboards(response?.shared_dashboards || []);
    setInvitations(response?.invitations || []);
    setSelectedDashboardId(
      (current) => current || requestedDashboardId || String(owned[0]?.id || "")
    );
  }

  async function loadCollaborators(dashboardId) {
    if (!dashboardId) {
      setCollaborators([]);
      return;
    }

    const response = await getDashboardCollaborators(getToken(), dashboardId);
    setCollaborators(response?.collaborators || []);
  }

  useEffect(() => {
    const timeout = setTimeout(() => {
      loadOverview()
        .catch((err) => toast.error(err.message))
        .finally(() => setLoading(false));
    }, 0);

    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      loadCollaborators(selectedDashboardId).catch((err) =>
        toast.error(err.message)
      );
    }, 0);

    return () => clearTimeout(timeout);
  }, [selectedDashboardId]);

  useEffect(() => {
    const trimmed = query.trim();

    if (trimmed.length < 2 || selectedUser) return;

    const timeout = setTimeout(() => {
      setSearchingUsers(true);
      searchUsers(getToken(), trimmed)
        .then((response) => setUsers(response?.users || []))
        .catch((err) => toast.error(err.message))
        .finally(() => setSearchingUsers(false));
    }, 250);

    return () => clearTimeout(timeout);
  }, [query, selectedUser]);

  async function handleShare(event) {
    event.preventDefault();

    if (!selectedDashboardId || !selectedUser) return;

    try {
      setSaving(true);
      await shareDashboard({
        token: getToken(),
        dashboard_id: selectedDashboardId,
        username: selectedUser.username,
        permission,
      });
      await loadCollaborators(selectedDashboardId);
      await loadOverview();
      setQuery("");
      setUsers([]);
      setSelectedUser(null);
      setSearchingUsers(false);
      notifyCollaborationChange();
      toast.success("Convite enviado com sucesso.");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleInvitation(collaborationId, response) {
    try {
      await respondInvitation(getToken(), collaborationId, response);
      await loadOverview();
      notifyCollaborationChange();
      toast.success(
        response === "accepted" ? "Convite aceito." : "Convite recusado."
      );
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function handlePermission(collaborationId, nextPermission) {
    try {
      await updateCollaboration({
        token: getToken(),
        collaboration_id: collaborationId,
        permission: nextPermission,
      });
      await loadCollaborators(selectedDashboardId);
      notifyCollaborationChange();
      toast.success("Permissao atualizada.");
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function handleRemove(collaborationId) {
    try {
      await deleteCollaboration(getToken(), collaborationId);
      await loadCollaborators(selectedDashboardId);
      await loadOverview();
      notifyCollaborationChange();
      toast.success("Acesso removido.");
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <AppLayout>
      <main className="collaborations-page">
        <section className="collaborations-hero">
          <div>
            <span>
              <UsersRound size={17} /> Colaboracoes
            </span>
            <h1>Compartilhe analises com sua equipe</h1>
            <p>
              Encontre pessoas pelo nome ou usuario e escolha exatamente o que
              elas podem fazer.
            </p>
          </div>
          <Share2 size={42} />
        </section>

        {loading ? (
          <Loading label="Carregando colaboracoes" />
        ) : (
          <section className="collaborations-grid">
            <div className="collaboration-card">
              <h2>Novo convite</h2>
              <form onSubmit={handleShare}>
                <label>
                  Dashboard
                  <select
                    value={selectedDashboardId}
                    onChange={(event) =>
                      setSelectedDashboardId(event.target.value)
                    }
                  >
                    <option value="">Selecione um dashboard</option>
                    {dashboards.map((dashboard) => (
                      <option key={dashboard.id} value={dashboard.id}>
                        {dashboard.title}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Buscar por nome ou usuario
                  <div className="collaboration-search">
                    <Search size={17} />
                    <input
                      value={query}
                      onChange={(event) => {
                        const value = event.target.value;
                        setQuery(value);
                        setSelectedUser(null);
                        if (value.trim().length < 2) {
                          setUsers([]);
                          setSearchingUsers(false);
                        }
                      }}
                      placeholder="@usuario ou nome"
                    />
                  </div>
                </label>

                {users.length > 0 && !selectedUser && (
                  <div className="collaboration-results">
                    {users.map((user) => (
                      <button
                        type="button"
                        key={user.user_id}
                        onClick={() => {
                          setSelectedUser(user);
                          setQuery(user.username);
                          setUsers([]);
                        }}
                      >
                        <ProfileAvatar
                          image={user.profile_image}
                          name={user.name}
                          size="large"
                        />
                        <span>
                          <strong>{user.name}</strong>
                          <small>@{user.username}</small>
                        </span>
                        <em>Escolher</em>
                      </button>
                    ))}
                  </div>
                )}

                {searchingUsers && !selectedUser && (
                  <p className="collaboration-empty">Buscando perfis...</p>
                )}

                {query.trim().length >= 2 &&
                  users.length === 0 &&
                  !searchingUsers &&
                  !selectedUser && (
                    <p className="collaboration-empty">
                      Nenhum perfil encontrado.
                    </p>
                  )}

                {selectedUser && (
                  <div className="selected-user-card">
                    <ProfileAvatar
                      image={selectedUser.profile_image}
                      name={selectedUser.name}
                      size="large"
                    />
                    <span>
                      <strong>{selectedUser.name}</strong>
                      <small>@{selectedUser.username}</small>
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedUser(null);
                        setQuery("");
                        setSearchingUsers(false);
                      }}
                    >
                      Trocar
                    </button>
                  </div>
                )}

                <div className="permission-grid">
                  {PERMISSIONS.map((item) => (
                    <button
                      type="button"
                      key={item.value}
                      className={`permission-button ${
                        permission === item.value ? "is-active" : ""
                      }`}
                      onClick={() => setPermission(item.value)}
                    >
                      <strong>{item.label}</strong>
                      <small>{item.description}</small>
                    </button>
                  ))}
                </div>

                <button
                  className="collaboration-primary"
                  disabled={saving || !selectedUser || !selectedDashboardId}
                >
                  <Share2 size={17} />{" "}
                  {saving ? "Enviando..." : "Enviar convite"}
                </button>
              </form>
            </div>

            <div className="collaboration-card">
              <h2>Convites recebidos</h2>
              {invitations.length === 0 ? (
                <p className="collaboration-empty">Nenhum convite pendente.</p>
              ) : (
                invitations.map((invitation) => (
                  <div className="collaborator-row" key={invitation.id}>
                    <ProfileAvatar
                      image={invitation.creator_profile_image}
                      name={invitation.creator_name}
                    />
                    <span>
                      <strong>{invitation.title}</strong>
                      <small>Convite de @{invitation.creator_username}</small>
                    </span>
                    <button
                      type="button"
                      className="invitation-accept"
                      onClick={() =>
                        handleInvitation(invitation.id, "accepted")
                      }
                      title="Aceitar"
                    >
                      <Check size={17} />
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        handleInvitation(invitation.id, "declined")
                      }
                      title="Recusar"
                    >
                      <X size={17} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </section>
        )}

        <section className="collaboration-card shared-overview">
          <h2>Pessoas com acesso</h2>
          {collaborators.length === 0 ? (
            <p className="collaboration-empty">
              Esse dashboard ainda nao foi compartilhado.
            </p>
          ) : (
            collaborators.map((person) => (
              <div className="collaborator-row" key={person.id}>
                <ProfileAvatar image={person.profile_image} name={person.name} />
                <span>
                  <strong>@{person.username}</strong>
                  <small>
                    {person.name} -{" "}
                    {person.status === "pending"
                      ? "Convite pendente"
                      : person.status === "declined"
                        ? "Convite recusado"
                        : "Acesso ativo"}
                  </small>
                </span>
                <select
                  value={person.permission}
                  onChange={(event) =>
                    handlePermission(person.id, event.target.value)
                  }
                >
                  {PERMISSIONS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="collaboration-delete-button"
                  onClick={() => handleRemove(person.id)}
                >
                  <Trash2 size={17} />
                </button>
              </div>
            ))
          )}
        </section>

        <section className="collaboration-card shared-overview">
          <h2>Compartilhados comigo</h2>
          {sharedDashboards.length === 0 ? (
            <p className="collaboration-empty">
              Nenhum dashboard compartilhado com voce ainda.
            </p>
          ) : (
            sharedDashboards.map((dashboard) => (
              <div className="collaborator-row" key={dashboard.id}>
                <ProfileAvatar
                  image={dashboard.creator_profile_image}
                  name={dashboard.creator_name}
                />
                <span>
                  <strong>{dashboard.title}</strong>
                  <small>Criado por @{dashboard.creator_username}</small>
                </span>
                <em>
                  {
                    PERMISSIONS.find(
                      (item) => item.value === dashboard.access_permission
                    )?.label
                  }
                </em>
                <button
                  type="button"
                  className="collaboration-delete-button"
                  onClick={() =>
                    handleRemove(dashboard.collaboration_id || dashboard.id)
                  }
                  title="Remover compartilhamento"
                >
                  <Trash2 size={17} />
                </button>
              </div>
            ))
          )}
        </section>
      </main>
    </AppLayout>
  );
}
