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
    let message =
      data?.detail ||
      data?.message ||
      data?.error ||
      text ||
      fallbackMessage;

    if (typeof message !== "string") {
      message = JSON.stringify(message);
    }

    if (isSessionExpiredError(message, response.status)) {
      handleExpiredSession(message);
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data || {};
}

async function safeFetch(url, options = {}, fallbackMessage) {
  try {
    const response = await fetch(url, {
      credentials: "include",
      ...options,
    });

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

function normalizeRefreshInterval(value) {
  if (value === "" || value === undefined || value === null) {
    return null;
  }

  return Number(value);
}

export async function createDataSource({
  token: _token,
  name,
  sourceType = "file",
  file,
  apiUrl,
  apiPayload,
  databaseUrl,
  query,
  refreshIntervalDays,
}) {
  if (sourceType === "file") {
    const formData = new FormData();
    formData.append("name", name);
    formData.append("file", file);

    return safeFetch(
      `${ACCOUNTS_URL}/data-sources/file`,
      {
        method: "POST",
        body: formData,
      },
      "Erro ao enviar arquivo."
    );
  }

  if (sourceType === "database") {
    return safeFetch(
      `${ACCOUNTS_URL}/data-sources/sql`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          database_url: databaseUrl,
          query,
          refresh_interval_days: normalizeRefreshInterval(
            refreshIntervalDays
          ),
        }),
      },
      "Erro ao criar fonte SQL."
    );
  }

  const formData = new FormData();
  formData.append("token", _token || "");
  formData.append("name", name);
  formData.append("source_type", "web");
  formData.append("api_url", apiUrl || "");

  if (refreshIntervalDays) {
    formData.append(
      "refresh_interval_days",
      String(refreshIntervalDays)
    );
  }

  if (apiPayload !== undefined) {
    formData.append(
      "api_payload",
      JSON.stringify(apiPayload)
    );
  }

  return safeFetch(
    `${ACCOUNTS_URL}/data-source/create`,
    {
      method: "POST",
      body: formData,
    },
    "Erro ao criar fonte web."
  );
}

export async function getDataSources(_token) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/`,
    {
      method: "GET",
    },
    "Erro ao buscar fontes de dados."
  );
}

export async function getDataSource(_token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/${Number(data_source_id)}`,
    {
      method: "GET",
    },
    "Erro ao abrir fonte de dados."
  );
}

export async function getLinkedDashboards(_token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/linked-dashboards?data_source_id=${Number(
      data_source_id
    )}`,
    {
      method: "GET",
    },
    "Erro ao buscar dashboards vinculados."
  );
}

export async function updateDataSource({
  token: _token,
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
  const sourceId = Number(data_source_id);

  if (sourceType === "file") {
    const formData = new FormData();
    formData.append("file", file);

    return safeFetch(
      `${ACCOUNTS_URL}/data-sources/file?data_source_id=${sourceId}`,
      {
        method: "PATCH",
        body: formData,
      },
      "Erro ao atualizar arquivo."
    );
  }

  if (sourceType === "database") {
    return safeFetch(
      `${ACCOUNTS_URL}/data-sources/sql?data_source_id=${sourceId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          database_url: databaseUrl,
          query,
          refresh_interval_days: normalizeRefreshInterval(
            refreshIntervalDays
          ),
        }),
      },
      "Erro ao atualizar fonte SQL."
    );
  }

  const formData = new FormData();
  formData.append("token", _token || "");
  formData.append("data_source_id", sourceId);
  formData.append(
    "refresh_dashboards",
    String(refreshDashboards)
  );

  if (sourceType) {
    formData.append("source_type", sourceType);
  }

  if (refreshIntervalDays) {
    formData.append(
      "refresh_interval_days",
      String(refreshIntervalDays)
    );
  }

  if (apiUrl !== undefined) {
    formData.append("api_url", apiUrl || "");
  }

  if (apiPayload !== undefined) {
    formData.append(
      "api_payload",
      JSON.stringify(apiPayload)
    );
  }

  return safeFetch(
    `${ACCOUNTS_URL}/data-source/update`,
    {
      method: "PATCH",
      body: formData,
    },
    "Erro ao atualizar fonte web."
  );
}

export async function executeSqlDataSource({
  data_source_id,
  query,
  saveQuery = false,
}) {
  const sourceId = Number(data_source_id);

  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/sql/execute?data_source_id=${sourceId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query || null,
        save_query: Boolean(saveQuery),
      }),
    },
    "Erro ao executar consulta SQL."
  );
}

export async function renameDataSource({
  token: _token,
  data_source_id,
  name,
}) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/?data_source_id=${Number(
      data_source_id
    )}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    },
    "Erro ao renomear fonte de dados."
  );
}

export async function deleteDataSource(_token, data_source_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/data-sources/?data_source_id=${Number(
      data_source_id
    )}`,
    {
      method: "DELETE",
    },
    "Erro ao deletar fonte de dados."
  );
}
