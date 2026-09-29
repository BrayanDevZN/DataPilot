import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";

import { createUser, login } from "../api/accountsApi";
import {
  getRegisterData,
  removeRegisterData,
  saveToken,
} from "../utils/storage";

export default function RegisterCode() {
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreate(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const registerData = getRegisterData();

      if (!registerData) {
        throw new Error("Dados de cadastro não encontrados.");
      }

      const payload = {
        ...registerData,
        age: Number(registerData.age),
        code: Number(code),
      };

      await createUser(payload);

      const response = await login(
        registerData.email,
        registerData.password
      );

      const token =
        response?.token ||
        response?.access_token ||
        response?.data?.token;

      if (!token) {
        throw new Error("Codigo invalido.");
      }

      saveToken(token);
      removeRegisterData();

      navigate("/profile-photo-setup");
    } catch (err) {
      setError(err.message || "Erro ao criar conta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Confirmar cadastro"
      subtitle="Digite o código de 6 dígitos enviado para seu email."
    >
      <form className="code-form" onSubmit={handleCreate}>
        <Input
          label="Código"
          type="number"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Digite o código"
        />

        {error && <p className="error-message">{error}</p>}

        <Button type="submit" disabled={loading}>
          {loading ? "Criando conta..." : "Criar conta"}
        </Button>
      </form>
    </AuthLayout>
  );
}
