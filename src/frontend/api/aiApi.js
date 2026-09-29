import { handleExpiredSession, isSessionExpiredError } from "../utils/session";

const AI_URL = "https://web-production-40ead.up.railway.app";

export async function sendChatMessage({ token, conversation_id, question }) {
  const response = await fetch(`${AI_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token,
      conversation_id: Number(conversation_id),
      question,
    }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail || data?.message || "Erro ao chamar a IA";

    if (isSessionExpiredError(message, response.status)) {
      handleExpiredSession(message);
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}
