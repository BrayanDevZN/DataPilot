import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";

import { validUser, sendPasswordCode } from "../api/accountsApi";
import { saveResetEmail } from "../utils/storage";

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function validateEmail() {
    const cleanEmail = email.trim();

    if (!cleanEmail) return "Digite seu e-mail.";

    if (!cleanEmail.endsWith("@gmail.com")) {
      return "O e-mail precisa terminar com @gmail.com.";
    }

    return null;
  }

  async function handleNext(event) {
    event.preventDefault();

    setError("");

    const emailError = validateEmail();

    if (emailError) {
      setError(emailError);
      return;
    }

    setLoading(true);

    try {
      const cleanEmail = email.trim();

      const response = await validUser(cleanEmail);

      if (response?.exists !== true) {
        setError("Essa conta não existe.");
        return;
      }

      await sendPasswordCode(cleanEmail);

      saveResetEmail(cleanEmail);

      navigate("/forgot-password-code");
    } catch (err) {
      setError(err.message || "Erro ao verificar conta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Recuperar senha"
      subtitle="Digite seu e-mail para receber o código de recuperação."
    >
      <form className="forgot-form" onSubmit={handleNext}>
        <Input
          label="E-mail"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="exemplo@gmail.com"
        />

        {error && <p className="error-message">{error}</p>}

        <Button type="submit" disabled={loading}>
          {loading ? "Verificando..." : "Prosseguir"}
        </Button>

        <div className="auth-links">
          <Link to="/">Voltar ao login</Link>
        </div>
      </form>
    </AuthLayout>
  );
}