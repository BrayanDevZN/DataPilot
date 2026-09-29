import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  Pencil,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  UserPen,
  UserRound,
} from "lucide-react";

import AppLayout from "../components/AppLayout";
import ProfileAvatar from "../components/ProfileAvatar";

import { getToken, removeToken } from "../utils/storage";
import { fileToProfileImage } from "../utils/profileImage";
import {
  getMe,
  updateName,
  updateProfileImage,
  updatePassword,
  updateUsername,
  deleteAccount,
} from "../api/accountsApi";

export default function Settings() {
  const navigate = useNavigate();

  const [currentName, setCurrentName] = useState("Carregando...");
  const [name, setName] = useState("");
  const [currentUsername, setCurrentUsername] = useState("");
  const [username, setUsername] = useState("");
  const [profileImage, setProfileImage] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  const [showPasswordWarning, setShowPasswordWarning] = useState(false);

  const [showDeleteWarning, setShowDeleteWarning] = useState(false);
  const [showDeletePasswordModal, setShowDeletePasswordModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [showDeletePassword, setShowDeletePassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingName, setLoadingName] = useState(false);
  const [loadingUsername, setLoadingUsername] = useState(false);
  const [loadingPhoto, setLoadingPhoto] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);

  async function loadProfile() {
    try {
      setLoadingProfile(true);

      const token = getToken();

      if (!token) {
        navigate("/");
        return;
      }

      const response = await getMe(token);

      if (response?.status === false || !response?.user) {
        throw new Error("Não foi possível carregar os dados do perfil.");
      }

      setCurrentName(response.user.name || "Não informado");
      setCurrentUsername(response.user.username || "");
      setProfileImage(response.user.profile_image || "");
    } catch (err) {
      console.error("Erro ao carregar perfil:", err);
      setCurrentName("Não informado");
      setError(err.message || "Erro ao carregar perfil.");
    } finally {
      setLoadingProfile(false);
    }
  }

  function validatePassword(password) {
    if (password.length < 8) return "A senha precisa ter pelo menos 8 caracteres.";
    if (!/[A-Z]/.test(password)) return "A senha precisa ter pelo menos uma letra maiúscula.";
    if (!/[a-z]/.test(password)) return "A senha precisa ter pelo menos uma letra minúscula.";
    if (!/[0-9]/.test(password)) return "A senha precisa ter pelo menos um número.";
    return null;
  }

  async function handleUpdateName(event) {
    event.preventDefault();

    const cleanName = name.trim();

    if (!cleanName) {
      setError("Digite um nome válido.");
      setSuccess("");
      return;
    }

    if (cleanName === currentName) {
      setError("O novo nome precisa ser diferente do nome atual.");
      setSuccess("");
      return;
    }

    setError("");
    setSuccess("");
    setLoadingName(true);

    try {
      const token = getToken();
      const response = await updateName(token, cleanName);

      if (response?.status === false) {
        throw new Error("Não foi possível atualizar o nome.");
      }

      setCurrentName(cleanName);
      setSuccess("Nome atualizado com sucesso.");
      setName("");
    } catch (err) {
      setError(err.message || "Erro ao atualizar nome.");
    } finally {
      setLoadingName(false);
    }
  }

  async function handleUpdateUsername(event) {
    event.preventDefault();

    const cleanUsername = username.trim().toLowerCase();

    if (!/^[a-zA-Z0-9_]{3,30}$/.test(cleanUsername)) {
      setError("Use de 3 a 30 caracteres: letras, números ou _.");
      setSuccess("");
      return;
    }

    if (cleanUsername === currentUsername) {
      setError("O novo nome de usuário precisa ser diferente do atual.");
      setSuccess("");
      return;
    }

    try {
      setLoadingUsername(true);
      setError("");
      setSuccess("");

      const response = await updateUsername(getToken(), cleanUsername);

      if (response?.status === "exists") {
        throw new Error("Esse nome de usuário já está em uso.");
      }

      if (response?.status === false) {
        throw new Error("Não foi possível atualizar o nome de usuário.");
      }

      setCurrentUsername(cleanUsername);
      setUsername("");
      setSuccess("Nome de usuário atualizado com sucesso.");
    } catch (err) {
      setError(err.message || "Erro ao atualizar nome de usuário.");
    } finally {
      setLoadingUsername(false);
    }
  }

  async function handleProfileImageChange(event) {
    try {
      setLoadingPhoto(true);
      setError("");
      setSuccess("");

      const nextImage = await fileToProfileImage(event.target.files[0]);
      const response = await updateProfileImage(getToken(), nextImage);

      if (response?.status === false) {
        throw new Error(response?.message || "Não foi possível atualizar sua foto.");
      }

      setProfileImage(nextImage);
      setSuccess("Foto de perfil atualizada com sucesso.");
    } catch (err) {
      setError(err.message || "Erro ao atualizar foto.");
    } finally {
      setLoadingPhoto(false);
      event.target.value = "";
    }
  }

  function handlePasswordSubmit(event) {
    event.preventDefault();

    if (!currentPassword.trim()) {
      setError("Digite sua senha atual.");
      setSuccess("");
      return;
    }

    const passwordError = validatePassword(newPassword);

    if (passwordError) {
      setError(passwordError);
      setSuccess("");
      return;
    }

    setError("");
    setSuccess("");
    setShowPasswordWarning(true);
  }

  async function confirmUpdatePassword() {
    setLoadingPassword(true);
    setShowPasswordWarning(false);

    try {
      const token = getToken();
      const response = await updatePassword(token, currentPassword, newPassword);

      if (response?.status === "equal") {
        throw new Error("A nova senha não pode ser igual à senha atual.");
      }

      if (response?.status === false) {
        throw new Error("Senha atual incorreta ou senha não atualizada.");
      }

      setSuccess("Senha atualizada com sucesso. Faça login novamente.");
      setCurrentPassword("");
      setNewPassword("");

      setTimeout(() => {
        removeToken();
        navigate("/");
      }, 1200);
    } catch (err) {
      setError(err.message || "Erro ao atualizar senha.");
    } finally {
      setLoadingPassword(false);
    }
  }

  function cancelUpdatePassword() {
    if (loadingPassword) return;
    setShowPasswordWarning(false);
  }

  function openDeleteWarning() {
    setError("");
    setSuccess("");
    setShowDeleteWarning(true);
  }

  function continueDeleteAccount() {
    setShowDeleteWarning(false);
    setShowDeletePasswordModal(true);
  }

  function cancelDeleteAccount() {
    if (loadingDelete) return;

    setShowDeleteWarning(false);
    setShowDeletePasswordModal(false);
    setDeletePassword("");
    setShowDeletePassword(false);
  }

  async function confirmDeleteAccount(event) {
    event.preventDefault();

    if (!deletePassword.trim()) {
      setError("Digite sua senha para confirmar.");
      return;
    }

    setLoadingDelete(true);
    setError("");
    setSuccess("");

    try {
      const token = getToken();

      if (!token) {
        navigate("/");
        return;
      }

      const response = await deleteAccount(token, deletePassword);

      if (response?.status === false) {
        throw new Error("Senha incorreta ou conta não deletada.");
      }

      removeToken();
      navigate("/");
    } catch (err) {
      setError(err.message || "Erro ao deletar conta.");
    } finally {
      setLoadingDelete(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  const passwordChecks = [
    { label: "Mínimo de 8 caracteres", active: newPassword.length >= 8 },
    { label: "Uma letra maiúscula", active: /[A-Z]/.test(newPassword) },
    { label: "Uma letra minúscula", active: /[a-z]/.test(newPassword) },
    { label: "Um número", active: /[0-9]/.test(newPassword) },
  ];

  return (
    <AppLayout>
      <main className="settings-page settings-datapilot-page">
        <section className="settings-dp-hero">
          <div>
            <span className="settings-dp-kicker">DataPilot AI</span>
            <h1>Configurações</h1>
            <p>Gerencie os dados do perfil, senha de acesso e segurança da sua conta.</p>
          </div>
        </section>

        {(error || success) && (
          <div className={`settings-dp-alert ${error ? "settings-dp-alert-error" : "settings-dp-alert-success"}`}>
            {error ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
            <span>{error || success}</span>
          </div>
        )}

        <section className="settings-dp-grid">
          <div className="settings-dp-main">
            <section className="settings-dp-card settings-profile-photo-card">
              <header className="settings-dp-card-header">
                <span className="settings-dp-icon-box settings-dp-icon-blue">
                  <UserRound size={22} />
                </span>

                <div>
                  <h2>Foto de perfil</h2>
                  <p>Escolha a imagem que representa você na plataforma.</p>
                </div>
              </header>

              <div className="settings-profile-photo-row">
                <div className="profile-photo-editor">
                  <ProfileAvatar image={profileImage} name={currentName} size="large" />

                  <label className="profile-photo-edit-button" title="Alterar foto de perfil">
                    <Pencil size={16} />
                    <input type="file" accept="image/*" onChange={handleProfileImageChange} disabled={loadingPhoto} />
                  </label>
                </div>

                <div>
                  <strong>{loadingPhoto ? "Atualizando foto..." : "Sua foto de perfil"}</strong>
                  <p>Formatos de imagem comuns, com até 5 MB.</p>
                </div>
              </div>
            </section>

            <form className="settings-dp-card" onSubmit={handleUpdateName}>
              <header className="settings-dp-card-header">
                <span className="settings-dp-icon-box settings-dp-icon-blue">
                  <UserPen size={22} />
                </span>

                <div>
                  <h2>Perfil</h2>
                  <p>Atualize o nome exibido na sua conta.</p>
                </div>
              </header>

              <div className="settings-dp-current-box">
                <span>Nome atual</span>
                <strong>{loadingProfile ? "Carregando..." : currentName}</strong>
              </div>

              <label className="settings-label settings-dp-field">
                Novo nome
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Digite seu novo nome"
                />
              </label>

              <div className="settings-dp-actions">
                <button
                  type="submit"
                  className="settings-dp-primary-button"
                  disabled={loadingName || loadingProfile}
                >
                  {loadingName ? "Atualizando..." : "Atualizar nome"}
                </button>
              </div>
            </form>

            <form className="settings-dp-card" onSubmit={handleUpdateUsername}>
              <header className="settings-dp-card-header">
                <span className="settings-dp-icon-box settings-dp-icon-navy">
                  <UserRound size={22} />
                </span>

                <div>
                  <h2>Nome de usuário</h2>
                  <p>Seu identificador único dentro da plataforma.</p>
                </div>
              </header>

              <div className="settings-dp-current-box">
                <span>Nome de usuário atual</span>
                <strong>@{currentUsername || "usuario"}</strong>
              </div>

              <label className="settings-label settings-dp-field">
                Novo nome de usuário
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="Ex: brayan_dev"
                />
              </label>

              <div className="settings-dp-actions">
                <button type="submit" className="settings-dp-primary-button" disabled={loadingUsername || loadingProfile}>
                  {loadingUsername ? "Atualizando..." : "Atualizar nome de usuário"}
                </button>
              </div>
            </form>

            <form className="settings-dp-card" onSubmit={handlePasswordSubmit}>
              <header className="settings-dp-card-header">
                <span className="settings-dp-icon-box settings-dp-icon-navy">
                  <LockKeyhole size={22} />
                </span>

                <div>
                  <h2>Alterar senha</h2>
                  <p>Escolha uma senha forte para proteger o acesso ao sistema.</p>
                </div>
              </header>

              <div className="settings-dp-password-rules">
                {passwordChecks.map((check) => (
                  <span key={check.label} className={check.active ? "is-valid" : ""}>
                    <CheckCircle2 size={14} />
                    {check.label}
                  </span>
                ))}
              </div>

              <label className="settings-label settings-dp-field">
                Senha atual
                <div className="password-row settings-dp-password-row">
                  <input
                    type={showCurrentPassword ? "text" : "password"}
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                    placeholder="Digite sua senha atual"
                  />

                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword((prev) => !prev)}
                    aria-label={showCurrentPassword ? "Ocultar senha atual" : "Mostrar senha atual"}
                  >
                    {showCurrentPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    <span>{showCurrentPassword ? "Ocultar" : "Mostrar"}</span>
                  </button>
                </div>
              </label>

              <label className="settings-label settings-dp-field">
                Nova senha
                <div className="password-row settings-dp-password-row">
                  <input
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    placeholder="Digite a nova senha"
                  />

                  <button
                    type="button"
                    onClick={() => setShowNewPassword((prev) => !prev)}
                    aria-label={showNewPassword ? "Ocultar nova senha" : "Mostrar nova senha"}
                  >
                    {showNewPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    <span>{showNewPassword ? "Ocultar" : "Mostrar"}</span>
                  </button>
                </div>
              </label>

              <div className="settings-dp-actions settings-dp-actions-between">
                <Link className="settings-dp-recover-link" to="/settings/recover-password">
                  <Mail size={16} />
                  Recuperar por email
                </Link>

                <button
                  type="submit"
                  className="settings-dp-primary-button"
                  disabled={loadingPassword}
                >
                  {loadingPassword ? "Atualizando..." : "Atualizar senha"}
                </button>
              </div>
            </form>

            <section className="settings-dp-card settings-dp-danger-card">
              <header className="settings-dp-card-header">
                <span className="settings-dp-icon-box settings-dp-icon-danger">
                  <ShieldAlert size={22} />
                </span>

                <div>
                  <h2>Excluir conta</h2>
                  <p>Essa ação remove sua conta e seus dados permanentemente.</p>
                </div>
              </header>

              <div className="settings-dp-danger-row">
                <div>
                  <strong>Zona de risco</strong>
                  <span>Depois de deletar a conta, não será possível recuperar as informações.</span>
                </div>

                <button
                  type="button"
                  className="settings-dp-danger-button"
                  onClick={openDeleteWarning}
                >
                  <Trash2 size={17} />
                  Deletar conta
                </button>
              </div>
            </section>
          </div>

          <aside className="settings-dp-side">
            <section className="settings-dp-card settings-dp-account-card">
              <div className="profile-photo-editor">
                <ProfileAvatar image={profileImage} name={currentName} size="large" />

                <label className="profile-photo-edit-button" title="Alterar foto de perfil">
                  <Pencil size={15} />
                  <input type="file" accept="image/*" onChange={handleProfileImageChange} disabled={loadingPhoto} />
                </label>
              </div>

              <h3>{loadingProfile ? "Carregando..." : currentName}</h3>
              <p>@{currentUsername || "usuario"}</p>

              <div className="settings-dp-status-list">
                <span>
                  <CheckCircle2 size={15} />
                  Conta ativa
                </span>
                <span>
                  <ShieldCheck size={15} />
                  Segurança padrão
                </span>
              </div>
            </section>
          </aside>
        </section>
      </main>

      {showPasswordWarning && (
        <div className="modal-overlay">
          <div className="delete-modal-card">
            <div className="modal-icon">
              <LockKeyhole size={22} />
            </div>
            <h2>Atualizar senha</h2>

            <p>
              Ao atualizar sua senha, você será deslogado automaticamente e
              precisará entrar novamente.
            </p>

            <div className="delete-modal-actions">
              <button
                type="button"
                className="modal-cancel"
                onClick={cancelUpdatePassword}
                disabled={loadingPassword}
              >
                Cancelar
              </button>

              <button
                type="button"
                className="modal-confirm"
                onClick={confirmUpdatePassword}
                disabled={loadingPassword}
              >
                {loadingPassword ? "Atualizando..." : "Continuar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteWarning && (
        <div className="modal-overlay">
          <div className="delete-modal-card">
            <div className="modal-icon modal-icon-danger">
              <Trash2 size={22} />
            </div>
            <h2>Deletar conta</h2>

            <p>
              Essa ação vai apagar sua conta e seus dados. Depois disso, não dá
              para recuperar.
            </p>

            <div className="delete-modal-actions">
              <button
                type="button"
                className="modal-cancel"
                onClick={cancelDeleteAccount}
              >
                Cancelar
              </button>

              <button
                type="button"
                className="delete-confirm-button"
                onClick={continueDeleteAccount}
              >
                Continuar
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeletePasswordModal && (
        <div className="modal-overlay">
          <form className="delete-modal-card" onSubmit={confirmDeleteAccount}>
            <div className="modal-icon modal-icon-danger">
              <ShieldAlert size={22} />
            </div>
            <h2>Confirmar senha</h2>

            <p>Digite sua senha atual para confirmar a exclusão da conta.</p>

            <label className="settings-label">
              Senha
              <div className="password-row settings-dp-password-row">
                <input
                  type={showDeletePassword ? "text" : "password"}
                  value={deletePassword}
                  onChange={(event) => setDeletePassword(event.target.value)}
                  placeholder="Digite sua senha"
                />

                <button
                  type="button"
                  onClick={() => setShowDeletePassword((prev) => !prev)}
                  aria-label={showDeletePassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showDeletePassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  <span>{showDeletePassword ? "Ocultar" : "Mostrar"}</span>
                </button>
              </div>
            </label>

            <div className="delete-modal-actions">
              <button
                type="button"
                className="modal-cancel"
                onClick={cancelDeleteAccount}
                disabled={loadingDelete}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="delete-confirm-button"
                disabled={loadingDelete}
              >
                {loadingDelete ? "Deletando..." : "Deletar conta"}
              </button>
            </div>
          </form>
        </div>
      )}
    </AppLayout>
  );
}
