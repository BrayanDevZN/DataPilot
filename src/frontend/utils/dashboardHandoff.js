const CREATED_DASHBOARD_HANDOFF_KEY = "datapilot_created_dashboard";

function normalizeCreatedDashboardPayload(payload) {
  const dashboard = payload?.dashboard || payload;

  if (!dashboard?.id) return null;

  return {
    ...dashboard,
    charts: dashboard.charts || payload?.charts || [],
    ai_suggestion:
      dashboard.ai_suggestion ||
      payload?.ai_suggestion ||
      "",
  };
}

export function saveCreatedDashboardHandoff(payload) {
  const dashboard = normalizeCreatedDashboardPayload(payload);

  if (!dashboard) return;

  sessionStorage.setItem(
    CREATED_DASHBOARD_HANDOFF_KEY,
    JSON.stringify({
      dashboard_id: Number(dashboard.id),
      dashboard,
      created_at: Date.now(),
    })
  );
}

export function takeCreatedDashboardHandoff(dashboardId) {
  const expectedId = Number(dashboardId);
  const rawValue = sessionStorage.getItem(CREATED_DASHBOARD_HANDOFF_KEY);

  if (!rawValue || !expectedId) return null;

  try {
    const parsed = JSON.parse(rawValue);
    const isFresh = Date.now() - Number(parsed.created_at || 0) < 120000;
    const matchesDashboard = Number(parsed.dashboard_id) === expectedId;

    if (!isFresh || !matchesDashboard) {
      return null;
    }

    sessionStorage.removeItem(CREATED_DASHBOARD_HANDOFF_KEY);
    return parsed.dashboard || null;
  } catch {
    sessionStorage.removeItem(CREATED_DASHBOARD_HANDOFF_KEY);
    return null;
  }
}
