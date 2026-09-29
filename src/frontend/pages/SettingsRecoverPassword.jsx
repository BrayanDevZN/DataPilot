import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AppLayout from "../components/AppLayout";
import Button from "../components/Button";

import { getToken, removeToken } from "../utils/storage";
import {
  sendPasswordCodeByToken,
  updateAuthPasswordByToken,
} from "../api/accountsApi";

export default function SettingsRecoverPassword() {
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [emailMessage, setEmailMessage] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showLogoutWarning, setShowLogoutWarning] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingCode, setLoadingCode] = useState(false);
  const [loadingUpdate, setLoadingUpdate] = useState(false);

  function validatePassword(value) {
    if (value.length < 8) return "A senha precisa ter pelo menos 8 caracteres.";
    if (!/[A-Z]/.test(value)) return "A senha precisa ter pelo menos uma letra maiúscula.";
    if (!/[a-z]/.test(value)) return "A senha precisa ter pelo menos uma letra minúscula.";
    if (!/[0-9]/.test(value)) return "A senha precisa ter pelo menos um número.";
    return null;
  }

  async function handleSendCode() {
    setError("");
    setSuccess("");
    setLoadingCode(true);

    try {
      const token = getToken();

      if (!token) {
        navigate("/");
        return;
      }

      const response = await sendPasswordCodeByToken(token);

      const email =
        response?.email ||
        response?.user?.email ||
        "seu email cadastrado";

      setEmailMessage(`Código enviado para o email ${email}.`);
      setSuccess("Verifique sua caixa de entrada.");
    } catch (err) {
      setError(err.message || "Erro ao enviar código.");
    } finally {
      setLoadingCode(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!code.trim()) {
      setError("Digite o código recebido.");
      return;
    }

    const passwordError = validatePassword(password);

    if (passwordError) {
      setError(passwordError);
      return;
    }

    setShowLogoutWarning(true);
  }

  async function confirmUpdatePassword() {
    setLoadingUpdate(true);
    setShowLogoutWarning(false);

    try {
      const token = getToken();

      if (!token) {
        navigate("/");
        return;
      }

      const response = await updateAuthPasswordByToken(
        token,
        Number(code),
        password
      );

      if (response?.status === "equal") {
        throw new Error("A nova senha não pode ser igual à senha atual.");
      }

      if (response?.status !== true) {
        throw new Error("Código inválido, expirado ou senha não atualizada.");
      }

      setSuccess("Senha atualizada com sucesso. Faça login novamente.");

      setTimeout(() => {
        removeToken();
        navigate("/");
      }, 1200);
    } catch (err) {
      setError(err.message || "Erro ao atualizar senha.");
    } finally {
      setLoadingUpdate(false);
    }
  }

  return (
    <AppLayout>
      <main className="settings-page">
        <section className="settings-card">
          <div className="settings-header">
            <h1>Recuperar senha</h1>
            <p>Receba um código no email da sua conta para criar uma nova senha.</p>
          </div>

          {error && <p className="error-message">{error}</p>}
          {success && <p className="success-message">{success}</p>}
          {emailMessage && <p className="success-message">{emailMessage}</p>}

          <div className="settings-section">
            <div>
              <h2>Enviar código</h2>
              <p>O código será enviado para o email cadastrado na sua conta.</p>
            </div>

            <Button type="button" onClick={handleSendCode} disabled={loadingCode}>
              {loadingCode ? "Enviando..." : "Enviar código"}
            </Button>
          </div>

          <form className="settings-section" onSubmit={handleSubmit}>
            <div>
              <h2>Nova senha</h2>
              <p>Digite o código recebido e escolha uma nova senha.</p>

              <ul className="password-rules">
                <li>Mínimo de 8 caracteres</li>
                <li>Pelo menos uma letra maiúscula</li>
                <li>Pelo menos uma letra minúscula</li>
                <li>Pelo menos um número</li>
              </ul>
            </div>

            <label className="settings-label">
              Código
              <input
                value={code}
                onChange={(event) => setCode(event.target.value)}
                placeholder="Digite o código"
              />
            </label>

            <label className="settings-label">
              Nova senha
              <div className="password-row">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Digite a nova senha"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                >
                  {showPassword ? "Ocultar" : "Mostrar"}
                </button>
              </div>
            </label>

            <Button type="submit" disabled={loadingUpdate}>
              {loadingUpdate ? "Atualizando..." : "Atualizar senha"}
            </Button>
          </form>
        </section>
      </main>

      {showLogoutWarning && (
        <div className="modal-overlay">
          <div className="delete-modal-card">
            <h2>Atualizar senha</h2>

            <p>
              Ao atualizar sua senha, você será deslogado automaticamente e
              precisará entrar novamente.
            </p>

            <div className="delete-modal-actions">
              <button
                type="button"
                className="modal-cancel"
                onClick={() => setShowLogoutWarning(false)}
              >
                Cancelar
              </button>

              <button
                type="button"
                className="modal-confirm"
                onClick={confirmUpdatePassword}
              >
                Continuar
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}