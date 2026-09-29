import { handleExpiredSession, isSessionExpiredError } from "../utils/session";

const AI_URL = "https://web-production-40ead.up.railway.app";
const ACCOUNTS_URL = "https://web-production-81b91.up.railway.app";
const DASHBOARD_CREATION_POLL_ATTEMPTS = 36;
const DASHBOARD_CREATION_POLL_INTERVAL_MS = 5000;

async function parseResponse(response, fallbackMessage) {
  const text = await response.text().catch(() => "");
  let data;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    let message = fallbackMessage;

    if (typeof data?.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data?.detail)) {
      message = data.detail
        .map((err) => err.msg || JSON.stringify(err))
        .join(", ");
    } else if (data?.detail) {
      message = JSON.stringify(data.detail);
    } else if (data?.message) {
      message = data.message;
    } else if (data?.error) {
      message = data.error;
    } else if (text) {
      message = text;
    }

    console.log("ERRO COMPLETO DA API:", {
      status: response.status,
      statusText: response.statusText,
      body: data || text,
    });

    const error = new Error(message);
    error.status = response.status;

    if (isSessionExpiredError(error, response.status)) {
      handleExpiredSession(message);
    }

    throw error;
  }

  return data || {};
}

async function safeFetch(url, options, fallbackMessage) {
  try {
    console.log("CHAMANDO API:", url);

    const response = await fetch(url, options);

    return await parseResponse(response, fallbackMessage);
  } catch (error) {
    console.error("ERRO NO FETCH:", {
      url,
      error,
    });

    if (
      error?.message === "Failed to fetch" ||
      error instanceof TypeError
    ) {
      // eslint-disable-next-line preserve-caught-error
      throw new Error(
        "Não foi possível conectar com a API. Verifique se a API está online, se a URL está correta e se o CORS está liberado."
      );
    }

    throw error;
  }
}

function normalizeChartsPayload(data) {
  if (!data) return data;

  const charts =
    data.charts ||
    data.dashboard?.charts ||
    (data.chart ? [data.chart] : []);

  return {
    ...data,
    charts,
    dashboard: data.dashboard
      ? {
          ...data.dashboard,
          charts,
        }
      : data.dashboard,
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizeText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function isConnectionError(error) {
  const message = String(error?.message || "").toLowerCase();
  const status = Number(error?.status);

  return (
    error instanceof TypeError ||
    [502, 503, 504].includes(status) ||
    message.includes("failed to fetch") ||
    message.includes("nao foi possivel conectar") ||
    message.includes("não foi possível conectar") ||
    message.includes("networkerror") ||
    message.includes("load failed")
  );
}

function findCreatedDashboard(dashboards, title, dataSourceId, startedAt) {
  const cleanTitle = normalizeText(title);
  const sourceId = Number(dataSourceId);
  const startedTime = startedAt ? startedAt.getTime() : 0;

  return (dashboards || []).find((dashboard) => {
    const sameTitle = normalizeText(dashboard.title) === cleanTitle;
    const sameSource = Number(dashboard.data_source_id) === sourceId;

    if (!sameTitle || !sameSource) return false;

    const createdAt = dashboard.created_at || dashboard.updated_at;

    if (!createdAt || !startedTime) return true;

    return new Date(createdAt).getTime() >= startedTime - 60000;
  });
}

async function waitForCreatedDashboard({
  token,
  title,
  data_source_id,
  startedAt,
  onStatus,
}) {
  for (let attempt = 1; attempt <= DASHBOARD_CREATION_POLL_ATTEMPTS; attempt += 1) {
    if (onStatus && [1, 6, 12, 24].includes(attempt)) {
      onStatus("Aguardando a API confirmar o dashboard criado...");
    }

    await sleep(DASHBOARD_CREATION_POLL_INTERVAL_MS);

    let response;

    try {
      response = await getDashboards(token);
    } catch (error) {
      console.warn("Aguardando dashboard criado, mas a consulta falhou:", error);
      continue;
    }

    const dashboard = findCreatedDashboard(
      response?.dashboards || [],
      title,
      data_source_id,
      startedAt
    );

    if (dashboard?.id) {
      return normalizeChartsPayload({
        dashboard,
        charts: dashboard.charts || [],
      });
    }
  }

  return null;
}

export async function generateDashboard({
  token,
  title,
  prompt,
  data_source_id,
  onStatus,
}) {
  const startedAt = new Date();
  let lastStatusMessage = "";

  function emitStatus(message) {
    if (!onStatus || !message || message === lastStatusMessage) {
      return;
    }

    lastStatusMessage = message;
    onStatus(message);
  }

  function buildFormData() {
    const formData = new FormData();

    formData.append("token", token);
    formData.append("title", title);
    formData.append("prompt", prompt || "");
    formData.append("data_source_id", String(data_source_id));

    return formData;
  }

  async function generateWithStandardRequest() {
    try {
      const data = await safeFetch(
        `${AI_URL}/dashboard/analyze`,
        {
          method: "POST",
          body: buildFormData(),
        },
        "Erro ao gerar dashboard."
      );

      return normalizeChartsPayload(data);
    } catch (error) {
      if (!isConnectionError(error)) {
        throw error;
      }

      const createdDashboard = await waitForCreatedDashboard({
        token,
        title,
        data_source_id,
        startedAt,
        onStatus: emitStatus,
      });

      if (createdDashboard) {
        return createdDashboard;
      }

      throw error;
    }
  }

  if (onStatus && typeof ReadableStream !== "undefined") {
    let response;

    try {
      response = await fetch(`${AI_URL}/dashboard/analyze/stream`, {
        method: "POST",
        body: buildFormData(),
      });
    } catch (error) {
      if (!isConnectionError(error)) {
        throw error;
      }

      const createdDashboard = await waitForCreatedDashboard({
        token,
        title,
        data_source_id,
        startedAt,
        onStatus: emitStatus,
      });

      if (createdDashboard) {
        return createdDashboard;
      }

      throw error;
    }

    if (!response.ok || !response.body) {
      try {
        return normalizeChartsPayload(
          await parseResponse(response, "Erro ao gerar dashboard.")
        );
      } catch (error) {
        if (!isConnectionError(error)) {
          throw error;
        }

        const createdDashboard = await waitForCreatedDashboard({
          token,
          title,
          data_source_id,
          startedAt,
          onStatus: emitStatus,
        });

        if (createdDashboard) {
          return createdDashboard;
        }

        throw error;
      }
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalData = null;

    try {
      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;

          const event = JSON.parse(line);

          if (event.type === "status") {
            emitStatus(event.message);
          }

          if (event.type === "error") {
            const error = new Error(event.message || "Erro ao gerar dashboard.");

            if (isSessionExpiredError(error)) {
              handleExpiredSession(error.message);
            }

            throw error;
          }

          if (event.type === "complete") {
            finalData = normalizeChartsPayload(event.data);
            await reader.cancel().catch(() => {});
            return finalData;
          }
        }
      }
    } catch (error) {
      if (!isConnectionError(error)) {
        throw error;
      }

      const createdDashboard = await waitForCreatedDashboard({
        token,
        title,
        data_source_id,
        startedAt,
        onStatus: emitStatus,
      });

      if (createdDashboard) {
        return createdDashboard;
      }

      throw error;
    }

    if (buffer.trim()) {
      const event = JSON.parse(buffer);

      if (event.type === "complete") {
        finalData = event.data;
      }
    }

    if (!finalData) {
      const createdDashboard = await waitForCreatedDashboard({
        token,
        title,
        data_source_id,
        startedAt,
        onStatus: emitStatus,
      });

      if (createdDashboard) {
        return createdDashboard;
      }

      throw new Error("A API ainda nao confirmou o dashboard criado. Tente novamente em instantes.");
    }

    return normalizeChartsPayload(finalData);
  }

  return await generateWithStandardRequest();
}

export async function refreshDashboard({
  token,
  dashboard,
  prompt,
}) {
  if (!dashboard?.id) {
    throw new Error("Dashboard inválido.");
  }

  if (!dashboard?.data_source_id) {
    throw new Error("Este dashboard não está ligado a uma fonte de dados.");
  }

  const formData = new FormData();

  formData.append("token", token);
  formData.append("title", dashboard.title || "Dashboard");
  const refreshPrompt = prompt ?? dashboard.prompt ?? "";

  formData.append("prompt", refreshPrompt);
  formData.append("data_source_id", String(dashboard.data_source_id));

  const analyzedData = normalizeChartsPayload(
    await safeFetch(
      `${AI_URL}/dashboard/refresh/analyze`,
      {
        method: "POST",
        body: formData,
      },
      "Erro ao atualizar análise do dashboard."
    )
  );

  const savedData = await safeFetch(
    `${ACCOUNTS_URL}/dashboard/refresh/finish`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        dashboard_id: Number(dashboard.id),
        prompt: refreshPrompt,
        ai_suggestion:
          analyzedData.ai_suggestion ||
          analyzedData.dashboard?.ai_suggestion ||
          analyzedData.answer ||
          "",
        charts:
          analyzedData.charts ||
          analyzedData.dashboard?.charts ||
          [],
      }),
    },
    "Erro ao salvar atualização do dashboard."
  );

  return normalizeChartsPayload(savedData);
}

export async function refreshDashboards({
  token,
  dashboards,
}) {
  const results = [];

  for (const dashboard of dashboards || []) {
    const result = await refreshDashboard({
      token,
      dashboard,
    });

    results.push(result);
  }

  return results;
}

export async function getDashboards(token) {
  return safeFetch(
    `${ACCOUNTS_URL}/dashboards`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
    },
    "Erro ao buscar dashboards."
  );
}

export async function getDashboard(token, dashboard_id) {
  const data = await safeFetch(
    `${ACCOUNTS_URL}/dashboard`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        dashboard_id: Number(dashboard_id),
      }),
    },
    "Erro ao abrir dashboard."
  );

  return normalizeChartsPayload(data);
}

export async function deleteDashboard(token, dashboard_id) {
  return safeFetch(
    `${ACCOUNTS_URL}/dashboard`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token,
        dashboard_id: Number(dashboard_id),
      }),
    },
    "Erro ao deletar dashboard."
  );
}

export async function saveChartSettings({
  token,
  dashboard_id,
  chart_id,
  chart_color,
  chart_background,
  x_axis_text_color,
  y_axis_text_color,
  grid_color,
  grid_style,
  bar_style,
  pie_colors,
  show_legend,
}) {
  const body = {
    token,
    dashboard_id: Number(dashboard_id),
    chart_color,
    chart_background,
    x_axis_text_color,
    y_axis_text_color,
    grid_color,
    grid_style,
    bar_style,
    pie_colors: Array.isArray(pie_colors) ? pie_colors : [],
    show_legend: show_legend ?? true,
  };

  if (chart_id) {
    body.chart_id = Number(chart_id);
  }

  return safeFetch(
    `${ACCOUNTS_URL}/dashboard/chart/settings`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
    "Erro ao salvar configurações do gráfico."
  );
}
