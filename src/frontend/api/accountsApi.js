import { handleExpiredSession, isSessionExpiredError } from "../utils/session";

const ACCOUNTS_URL = "https://web-production-81b91.up.railway.app";

function getErrorMessage(data) {
  if (!data) {
    return "Erro na requisição";
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (typeof data.message === "string") {
    return data.message;
  }

  if (typeof data.error === "string") {
    return data.error;
  }

  try {
    return JSON.stringify(data.detail || data);
  } catch {
    return "Erro na requisição";
  }
}

async function request(endpoint, options = {}) {
  const response = await fetch(`${ACCOUNTS_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = getErrorMessage(data);

    if (isSessionExpiredError(message, response.status)) {
      handleExpiredSession(message);
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

export function validUser(email) {
  return request("/valid_user", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function validUsername(username) {
  return request("/valid_username", {
    method: "POST",
    body: JSON.stringify({ username }),
  });
}

export function login(email, password) {
  return request("/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function sendCreateCode(email) {
  return request("/env_code_create", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function createUser(userData) {
  return request("/create_user", {
    method: "POST",
    body: JSON.stringify(userData),
  });
}

export function validToken(token) {
  return request("/valid_token", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function updatePassword(token, current_password, password) {
  return request("/update_pass", {
    method: "PATCH",
    body: JSON.stringify({
      token,
      current_password,
      password,
    }),
  });
}

export function updateName(token, name) {
  return request("/update_name", {
    method: "PATCH",
    body: JSON.stringify({ token, name }),
  });
}

export function updateUsername(token, username) {
  return request("/update_username", {
    method: "PATCH",
    body: JSON.stringify({ token, username }),
  });
}

export function updateProfileImage(token, profile_image) {
  return request("/update_profile_image", {
    method: "PATCH",
    body: JSON.stringify({ token, profile_image }),
  });
}

export function sendPasswordCode(email) {
  return request("/env_pass", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function updateAuthPassword(email, code, password) {
  return request("/update_auth_pass", {
    method: "PATCH",
    body: JSON.stringify({
      email,
      code,
      password,
    }),
  });
}

export function createConversation(token, title) {
  return request("/conversation/create", {
    method: "POST",
    body: JSON.stringify({
      token,
      title,
    }),
  });
}

export function getConversations(token) {
  return request("/conversations", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function getConversationMessages(token, conversation_id) {
  return request("/conversation/messages", {
    method: "POST",
    body: JSON.stringify({
      token,
      conversation_id: Number(conversation_id),
    }),
  });
}

export function saveConversationMessage({
  token,
  conversation_id,
  role,
  content,
}) {
  return request("/conversation", {
    method: "POST",
    body: JSON.stringify({
      token,
      conversation_id: Number(conversation_id),
      role,
      content,
    }),
  });
}
export function deleteConversation(token, conversation_id) {
  return request("/conversation", {
    method: "DELETE",
    body: JSON.stringify({
      token,
      conversation_id: Number(conversation_id),
    }),
  });
}

export function getMe(token) {
  return request("/me", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}
export function sendPasswordCodeByToken(token) {
  return request("/env_pass", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function updateAuthPasswordByToken(token, code, password) {
  return request("/update_auth_pass", {
    method: "PATCH",
    body: JSON.stringify({
      token,
      code,
      password,
    }),
  });
}
export function deleteAccount(token, password) {
  return request("/delete_user", {
    method: "DELETE",
    body: JSON.stringify({
      token,
      password,
    }),
  });
}
