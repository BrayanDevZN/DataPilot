import { handleExpiredSession, isSessionExpiredError } from "../utils/session";

const ACCOUNTS_URL = "https://web-production-81b91.up.railway.app";

async function parseResponse(response, fallbackMessage) {
  const text = await response.text().catch(() => "");
  let data;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      data?.error ||
      text ||
      fallbackMessage;

    if (isSessionExpiredError(message, response.status)) {
      handleExpiredSession(message);
    }

    throw new Error(message);
  }

  return data || {};
}

async function safeFetch(url, options, fallbackMessage) {
  try {
    const response = await fetch(url, options);
    return await parseResponse(response, fallbackMessage);
  } catch (error) {
    if (
      error?.message === "Failed to fetch" ||
      error instanceof TypeError
    ) {
      throw new Error(
        "A requisição demorou ou a conexão foi interrompida. Atualize a lista para verificar se a ação foi concluída.",
        { cause: error }
      );
    }

    throw error;
  }
}

export async function createDataSource({
  token,
  name,
  sourceType = "file",
  file,
  apiUrl,
  apiPayload,
  databaseUrl,
  query,
  refreshIntervalDays,
}) {
  const formData = new FormData();

  formData.append("token", token);
  formData.append("name", name);
  formData.append("source_type", sourceType);

  if (refreshIntervalDays) {
    formData.append("refresh_interval_days", String(refreshIntervalDays));
  }

  if (sourceType === "file" && file) {
    formData.append("file", file);
  }

  if (sourceType === "web") {
    formData.append("api_url", apiUrl || "");

    if (apiPayload !== undefined) {
      formData.append("api_payload", JSON.stringify(apiPayload));
    }
  }

  if (sourceType === "database") {
    formData.append("database_url", databaseUrl || "");
    formData.append("query", query || "");
  }

  return safeFetch(
    `${ACCOUNTS_URL}/data-source/create`,
    {
      method: "POST",
      body: formData,
    },
    "Erro ao criar fonte de dados."
  );
}

export async function getDataSources(token) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
    },
    "Erro ao buscar fontes de dados."
  );
}

export async function getDataSource(token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-source`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        data_source_id: Number(data_source_id),
      }),
    },
    "Erro ao abrir fonte de dados."
  );
}

export async function getLinkedDashboards(token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-source/linked-dashboards`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        data_source_id: Number(data_source_id),
      }),
    },
    "Erro ao buscar dashboards vinculados."
  );
}

export async function updateDataSource({
  token,
  data_source_id,
  sourceType,
  file,
  apiUrl,
  apiPayload,
  databaseUrl,
  query,
  refreshIntervalDays,
  refreshDashboards = false,
}) {
  const formData = new FormData();

  formData.append("token", token);
  formData.append("data_source_id", Number(data_source_id));
  formData.append("refresh_dashboards", String(refreshDashboards));

  if (sourceType) {
    formData.append("source_type", sourceType);
  }

  if (refreshIntervalDays) {
    formData.append("refresh_interval_days", String(refreshIntervalDays));
  }

  if (file) {
    formData.append("file", file);
  }

  if (apiUrl !== undefined) {
    formData.append("api_url", apiUrl || "");
  }

  if (apiPayload !== undefined) {
    formData.append("api_payload", JSON.stringify(apiPayload));
  }

  if (databaseUrl !== undefined) {
    formData.append("database_url", databaseUrl || "");
  }

  if (query !== undefined) {
    formData.append("query", query || "");
  }

  return safeFetch(
    `${ACCOUNTS_URL}/data-source/update`,
    {
      method: "PATCH",
      body: formData,
    },
    "Erro ao atualizar fonte de dados."
  );
}

export async function renameDataSource({
  token,
  data_source_id,
  name,
}) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-source/rename`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        data_source_id: Number(data_source_id),
        name,
      }),
    },
    "Erro ao renomear fonte de dados."
  );
}

export async function deleteDataSource(token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-source`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        data_source_id: Number(data_source_id),
      }),
    },
    "Erro ao deletar fonte de dados."
  );
}
