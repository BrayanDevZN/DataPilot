import { UserRound } from "lucide-react";

export default function ProfileAvatar({
  image,
  name = "Usuário",
  size = "medium",
  className = "",
}) {
  return (
    <div className={`profile-avatar profile-avatar-${size} ${className}`.trim()}>
      {image ? (
        <img src={image} alt={`Foto de perfil de ${name}`} />
      ) : (
        <UserRound aria-hidden="true" />
      )}
    </div>
  );
}
