import { handleExpiredSession, isSessionExpiredError } from "../utils/session";

const ACCOUNTS_URL = "https://web-production-81b91.up.railway.app";

async function request(path, { method = "POST", body } = {}) {
  const response = await fetch(`${ACCOUNTS_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data?.detail || data?.message || "Erro ao processar colaboracao.";

    if (isSessionExpiredError(message, response.status)) {
      handleExpiredSession(message);
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

export function getCollaborationOverview(token) {
  return request("/collaborations", { body: { token } });
}

export function searchUsers(token, query) {
  return request("/users/search", { body: { token, query } });
}

export function getDashboardCollaborators(token, dashboard_id) {
  return request("/dashboard/collaborations", { body: { token, dashboard_id: Number(dashboard_id) } });
}

export function shareDashboard({ token, dashboard_id, username, permission }) {
  return request("/dashboard/collaboration/share", {
    body: { token, dashboard_id: Number(dashboard_id), username, permission },
  });
}

export function updateCollaboration({ token, collaboration_id, permission }) {
  return request("/dashboard/collaboration", {
    method: "PATCH",
    body: { token, collaboration_id: Number(collaboration_id), permission },
  });
}

export function deleteCollaboration(token, collaboration_id) {
  return request("/dashboard/collaboration", {
    method: "DELETE",
    body: { token, collaboration_id: Number(collaboration_id) },
  });
}

export function respondInvitation(token, collaboration_id, response) {
  return request("/dashboard/collaboration/respond", {
    body: { token, collaboration_id: Number(collaboration_id), response },
  });
}

export function getDashboardAccess(token, dashboard_id) {
  return request("/dashboard/access", {
    body: { token, dashboard_id: Number(dashboard_id) },
  });
}

export function getNotifications(token) {
  return request("/notifications", { body: { token } });
}

export function markNotificationRead(token, notification_id) {
  return request("/notification/read", {
    method: "PATCH",
    body: { token, notification_id: Number(notification_id) },
  });
}
