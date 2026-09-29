import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";

import { updateAuthPassword } from "../api/accountsApi";
import { getResetEmail, removeResetEmail } from "../utils/storage";

export default function ForgotPasswordCode() {
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  function validateForm() {
    if (!code.trim()) return "Digite o código.";
    if (code.trim().length !== 6) return "O código precisa ter 6 dígitos.";

    if (!password) return "Digite a nova senha.";
    if (password.length < 8) return "A senha precisa ter no mínimo 8 caracteres.";
    if (!/[A-Z]/.test(password)) return "A senha precisa ter uma letra maiúscula.";
    if (!/[a-z]/.test(password)) return "A senha precisa ter uma letra minúscula.";
    if (!/[0-9]/.test(password)) return "A senha precisa ter pelo menos um número.";

    return null;
  }

  async function handleUpdatePassword(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    const formError = validateForm();

    if (formError) {
      setError(formError);
      return;
    }

    setLoading(true);

    try {
      const email = getResetEmail();

      if (!email) {
        throw new Error("Email de recuperação não encontrado.");
      }

      const response = await updateAuthPassword(email, code.trim(), password);

      console.log("Resposta update_auth_pass:", response);

      if (response?.status !== true) {
        if (response?.status === "equal") {
          throw new Error("A nova senha não pode ser igual à senha atual.");
        }

        throw new Error("Código inválido, expirado ou senha não atualizada.");
      }

      removeResetEmail();

      setSuccess("Senha atualizada com sucesso.");

      setTimeout(() => {
        navigate("/");
      }, 1200);
    } catch (err) {
      setError(err.message || "Erro ao atualizar senha.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Nova senha"
      subtitle="Digite o código recebido e escolha sua nova senha."
    >
      <form className="code-form" onSubmit={handleUpdatePassword}>
        <Input
          label="Código"
          type="number"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Digite o código"
        />

        <div className="input-group">
          <label>Nova senha</label>

          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Digite a nova senha"
            />

            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
            >
              {showPassword ? "Ocultar" : "Mostrar"}
            </button>
          </div>
        </div>

        {error && <p className="error-message">{error}</p>}
        {success && <p className="success-message">{success}</p>}

        <Button type="submit" disabled={loading}>
          {loading ? "Atualizando..." : "Atualizar senha"}
        </Button>
      </form>
    </AuthLayout>
  );
}