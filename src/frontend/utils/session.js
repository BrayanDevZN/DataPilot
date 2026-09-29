import toast from "react-hot-toast";

import { logout } from "./storage";

let handlingExpiredSession = false;

export function isSessionExpiredError(errorOrMessage, status) {
  const message = String(
    typeof errorOrMessage === "string"
      ? errorOrMessage
      : errorOrMessage?.message || ""
  )
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  return (
    Number(status || errorOrMessage?.status) === 401 ||
    message.includes("sessao expirada") ||
    message.includes("token invalido") ||
    message.includes("invalid token")
  );
}

export function handleExpiredSession(message = "Sua sessao expirou. Faca login novamente.") {
  if (handlingExpiredSession) return;

  handlingExpiredSession = true;
  logout();
  toast.error(message);

  window.setTimeout(() => {
    window.location.assign("/");
  }, 900);
}
