import { useState } from "react";
import { Camera, Check, Pencil, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

import ProfileAvatar from "../components/ProfileAvatar";
import { updateProfileImage } from "../api/accountsApi";
import { getToken } from "../utils/storage";
import { fileToProfileImage } from "../utils/profileImage";

export default function ProfilePhotoSetup() {
  const navigate = useNavigate();

  const [profileImage, setProfileImage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleImageChange(event) {
    try {
      setError("");
      setProfileImage(await fileToProfileImage(event.target.files[0]));
    } catch (err) {
      setError(err.message || "Erro ao carregar imagem.");
    }
  }

  async function handleContinue() {
    try {
      setLoading(true);
      setError("");

      if (profileImage) {
        const response = await updateProfileImage(getToken(), profileImage);

        if (response?.status === false) {
          throw new Error(response?.message || "Não foi possível salvar sua foto.");
        }
      }

      navigate("/home");
    } catch (err) {
      setError(err.message || "Erro ao salvar foto.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="profile-setup-page">
      <section className="profile-setup-card">
        <span className="profile-setup-kicker">
          <Sparkles size={16} />
          Perfil criado
        </span>

        <div>
          <h1>Quer adicionar uma foto?</h1>
          <p>
            Sua foto ajuda a deixar a experiência mais pessoal. Essa etapa é
            opcional e você poderá alterá-la depois nas configurações.
          </p>
        </div>

        <div className="profile-photo-editor">
          <ProfileAvatar image={profileImage} size="xlarge" />

          <label className="profile-photo-edit-button" title="Escolher foto">
            <Pencil size={18} />
            <input type="file" accept="image/*" onChange={handleImageChange} />
          </label>
        </div>

        {error && <p className="error-message">{error}</p>}

        <div className="profile-setup-actions">
          <button type="button" className="profile-setup-skip" onClick={() => navigate("/home")} disabled={loading}>
            Agora não
          </button>

          <button type="button" className="profile-setup-primary" onClick={handleContinue} disabled={loading}>
            {profileImage ? <Check size={18} /> : <Camera size={18} />}
            {loading ? "Salvando..." : profileImage ? "Salvar e continuar" : "Continuar sem foto"}
          </button>
        </div>
      </section>
    </main>
  );
}
