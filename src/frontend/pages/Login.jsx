import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BarChart3, BrainCircuit, ShieldCheck } from "lucide-react";

import Input from "../components/Input";
import Button from "../components/Button";

import { validUser, login } from "../api/accountsApi";
import { getToken, saveToken } from "../utils/storage";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = getToken();

    if (token) {
      navigate("/home");
    }
  }, [navigate]);

  async function handleLogin(event) {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Digite seu e-mail.");
      return;
    }

    if (!password.trim()) {
      setError("Digite sua senha.");
      return;
    }

    setLoading(true);

    try {
      const normalizedEmail = email.trim().toLowerCase();
      const userResponse = await validUser(normalizedEmail);

      if (userResponse?.exists !== true) {
        throw new Error("Essa conta não existe.");
      }

      const response = await login(normalizedEmail, password);
      const token =
        response?.token || response?.access_token || response?.data?.token;

      if (!token) {
        throw new Error("E-mail ou senha inválidos.");
      }

      saveToken(token);
      navigate("/home");
    } catch (err) {
      setError(err.message || "Erro ao fazer login.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-left">
        <div className="brand login-brand">
          <img
            src="/favicon.svg"
            alt="Logo DataPilot AI"
            className="login-brand-logo"
          />

          <h1>
            DataPilot <span>AI</span>
          </h1>
        </div>

        <div className="hero-text">
          <h2>
            Gestão financeira <br />
            inteligente com <span>IA</span>
          </h2>

          <p>
            Envie planilhas, acompanhe dashboards e receba insights práticos
            para tomar decisões melhores.
          </p>
        </div>

        <div className="feature-list">
          <div className="feature-item">
            <div>
              <BarChart3 size={24} />
            </div>

            <span>
              <strong>Visualização financeira completa</strong>
              Gere análises, gráficos e relatórios de forma simples.
            </span>
          </div>

          <div className="feature-item">
            <div>
              <BrainCircuit size={24} />
            </div>

            <span>
              <strong>Copiloto financeiro com IA</strong>
              Receba respostas inteligentes a partir dos seus dados.
            </span>
          </div>

          <div className="feature-item">
            <div>
              <ShieldCheck size={24} />
            </div>

            <span>
              <strong>Segurança e privacidade</strong>
              Acesso protegido sem alterar sua estrutura de autenticação.
            </span>
          </div>
        </div>
      </section>

      <section className="login-right">
        <form className="login-card" onSubmit={handleLogin}>
          <h2>Bem-vindo de volta!</h2>
          <p>Faça login para acessar sua conta.</p>

          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="seu@email.com"
            autoComplete="email"
          />

          <div className="input-group">
            <label>Senha</label>

            <div className="password-field">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Digite sua senha"
                autoComplete="current-password"
              />

              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
              >
                {showPassword ? "Ocultar" : "Mostrar"}
              </button>
            </div>
          </div>

          <div className="login-options">
            <label>
              <input type="checkbox" defaultChecked />
              Lembrar de mim
            </label>

            <Link to="/forgot-password">Esqueci minha senha</Link>
          </div>

          {error && <p className="error-message">{error}</p>}

          <Button type="submit" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </Button>

          <div className="divider">
            <span>ou</span>
          </div>

          <p className="create-account">
            Ainda não tem uma conta? <Link to="/register">Criar conta</Link>
          </p>
        </form>

        <div className="secure-text">
          <strong>Seus dados protegidos com segurança</strong>
          <p>Utilizamos autenticação para proteger suas informações.</p>
        </div>
      </section>
    </main>
  );
}
