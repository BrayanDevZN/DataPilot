const DRILLABLE_CHART_TYPES = new Set([
  "bar",
  "horizontal_bar",
  "line",
  "area",
  "pie",
  "donut",
  "scatter",
]);

export function normalizeDrillKey(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function toNumber(value) {
  if (typeof value === "number") return Number.isNaN(value) ? 0 : value;

  const parsed = Number(
    String(value ?? "")
      .trim()
      .replace(/\./g, "")
      .replace(",", ".")
  );

  return Number.isNaN(parsed) ? 0 : parsed;
}

function normalizeHierarchyEntry(entry, rows) {
  if (!entry) return null;

  const keys = Object.keys(rows?.[0] || {});
  const rawColumn = typeof entry === "string" ? entry : entry.column;
  const label = typeof entry === "string" ? entry : entry.label || entry.column;
  const column = keys.find((key) => normalizeDrillKey(key) === normalizeDrillKey(rawColumn));

  if (!column) return null;

  return {
    column,
    label: label || column,
  };
}

function normalizeProvidedHierarchy(hierarchy, rows) {
  if (!Array.isArray(hierarchy)) return [];

  return hierarchy
    .map((entry) => normalizeHierarchyEntry(entry, rows))
    .filter(Boolean);
}

export function getDrillConfig(currentChart, rawData, xKey) {
  const chartType = currentChart?.chart_type || currentChart?.type || "bar";

  if (!DRILLABLE_CHART_TYPES.has(chartType)) {
    return { enabled: false, rows: [], hierarchy: [] };
  }

  const config = currentChart?.chart_config || currentChart?.config || {};
  const drillDown = config.drill_down || currentChart?.drill_down || {};

  if (drillDown.enabled !== true) {
    return { enabled: false, rows: [], hierarchy: [] };
  }

  const rows = Array.isArray(drillDown.rows) ? drillDown.rows : rawData;
  const providedHierarchy = drillDown.hierarchy || config.drill_down_hierarchy || currentChart?.drill_down_hierarchy;
  const normalizedProvided = normalizeProvidedHierarchy(providedHierarchy, rows);

  if (
    normalizedProvided.length >= 2 &&
    normalizeDrillKey(normalizedProvided[0].column) === normalizeDrillKey(xKey)
  ) {
    return {
      enabled: true,
      rows,
      hierarchy: normalizedProvided,
    };
  }

  return { enabled: false, rows: [], hierarchy: [] };
}

export function aggregateDrillRows({
  rows,
  hierarchy,
  path,
  yKey,
  sourceYKey,
  aggregation,
  operation,
  limit = 20,
  sort = "desc",
}) {
  if (!Array.isArray(rows) || !Array.isArray(hierarchy) || !hierarchy.length) {
    return [];
  }

  const currentLevel = Math.min(path.length, hierarchy.length - 1);
  const currentColumn = hierarchy[currentLevel]?.column;

  if (!currentColumn) return [];

  const filteredRows = rows.filter((row) =>
    path.every((entry) => String(row?.[entry.column] ?? "") === String(entry.value ?? ""))
  );

  const groups = new Map();

  filteredRows.forEach((row) => {
    const rawLabel = row?.[currentColumn];
    const label = rawLabel === null || rawLabel === undefined || rawLabel === "" ? "Sem valor" : String(rawLabel);
    const current = groups.get(label) || { total: 0, count: 0, values: [] };

    current.count += 1;

    if (operation === "count" || aggregation === "count" || !sourceYKey) {
      current.total += 1;
    } else {
      const value = toNumber(row?.[sourceYKey]);
      current.total += value;
      current.values.push(value);
    }

    groups.set(label, current);
  });

  const finalAggregation = Array.isArray(aggregation) ? aggregation[0] : aggregation;

  let data = Array.from(groups.entries()).map(([label, group]) => {
    let value = group.total;

    if (finalAggregation === "mean" && group.values.length) {
      value = group.total / group.values.length;
    } else if (finalAggregation === "max" && group.values.length) {
      value = Math.max(...group.values);
    } else if (finalAggregation === "min" && group.values.length) {
      value = Math.min(...group.values);
    } else if (finalAggregation === "median" && group.values.length) {
      const sorted = [...group.values].sort((a, b) => a - b);
      value = sorted[Math.floor(sorted.length / 2)];
    }

    return {
      [currentColumn]: label,
      [yKey || "Quantidade"]: value,
    };
  });

  if (sort === "asc" || sort === "desc") {
    data = data.sort((a, b) => {
      const left = toNumber(a[yKey || "Quantidade"]);
      const right = toNumber(b[yKey || "Quantidade"]);
      return sort === "asc" ? left - right : right - left;
    });
  }

  return data.slice(0, Math.max(1, Math.min(Number(limit) || 20, 100)));
}

export function canDrillDeeper(hierarchy, path) {
  return Array.isArray(hierarchy) && path.length < hierarchy.length - 1;
}
