import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";

import { validUser, validUsername, sendCreateCode } from "../api/accountsApi";
import { saveRegisterData } from "../utils/storage";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    username: "",
    email: "",
    age: "",
    gender: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(field, value) {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  }

  function validateForm() {
    const email = form.email.trim();
    const password = form.password;

    if (!form.name.trim()) return "Digite seu nome.";

    if (!/^[a-zA-Z0-9_]{3,30}$/.test(form.username.trim())) {
      return "O nome de usuário deve ter entre 3 e 30 caracteres e usar apenas letras, números ou _.";
    }

    if (!email) return "Digite seu email.";
    if (!email.endsWith("@gmail.com")) {
      return "O email precisa terminar com @gmail.com.";
    }

    if (!form.age || Number(form.age) <= 0) {
      return "Digite uma idade válida.";
    }

    if (!form.gender) {
      return "Selecione seu gênero.";
    }

    if (!password) return "Digite uma senha.";

    if (password.length < 8) {
      return "A senha precisa ter no mínimo 8 caracteres.";
    }

    if (!/[A-Z]/.test(password)) {
      return "A senha precisa ter pelo menos uma letra maiúscula.";
    }

    if (!/[a-z]/.test(password)) {
      return "A senha precisa ter pelo menos uma letra minúscula.";
    }

    if (!/[0-9]/.test(password)) {
      return "A senha precisa ter pelo menos um número.";
    }

    return null;
  }

  async function handleNext(event) {
    event.preventDefault();

    setError("");

    const formError = validateForm();

    if (formError) {
      setError(formError);
      return;
    }

    setLoading(true);

    try {
      const email = form.email.trim();

      const response = await validUser(email);

      if (response?.exists === true) {
        setError("Essa conta já existe.");
        return;
      }

      const username = form.username.trim().toLowerCase();
      const usernameResponse = await validUsername(username);

      if (usernameResponse?.exists === true) {
        setError("Esse nome de usuário já está em uso.");
        return;
      }

      await sendCreateCode(email);

      saveRegisterData({
        name: form.name.trim(),
        username,
        email,
        age: Number(form.age),
        gender: form.gender,
        password: form.password,
      });

      navigate("/register-code");
    } catch (err) {
      setError(err.message || "Erro ao iniciar cadastro.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Criar conta"
      subtitle="Preencha seus dados para acessar o agente."
    >
      <form className="register-form" onSubmit={handleNext}>
        <Input
          label="Nome"
          value={form.name}
          onChange={(e) => updateField("name", e.target.value)}
          placeholder="Digite seu nome"
        />

        <Input
          label="E-mail"
          type="email"
          value={form.email}
          onChange={(e) => updateField("email", e.target.value)}
          placeholder="exemplo@gmail.com"
        />

        <Input
          label="Nome de usuário"
          value={form.username}
          onChange={(e) => updateField("username", e.target.value)}
          placeholder="Ex: brayan_dev"
        />

        <Input
          label="Idade"
          type="number"
          value={form.age}
          onChange={(e) => updateField("age", e.target.value)}
          placeholder="Digite sua idade"
        />

        <div className="input-group">
          <label>Gênero</label>
          <select
            value={form.gender}
            onChange={(e) => updateField("gender", e.target.value)}
          >
            <option value="">Selecione</option>
            <option value="MASCULINO">Masculino</option>
            <option value="FEMININO">Feminino</option>
            <option value="PREFIRO NÃO DIZER">Prefiro não dizer</option>
          </select>
        </div>

        <div className="input-group">
          <label>Senha</label>

          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              placeholder="Crie sua senha"
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

        <Button type="submit" disabled={loading}>
          {loading ? "Enviando..." : "Prosseguir"}
        </Button>

        <div className="auth-links">
          <Link to="/">Já tenho conta</Link>
        </div>
      </form>
    </AuthLayout>
  );
}
