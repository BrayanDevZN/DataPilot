import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import toast from "react-hot-toast";
import { AlertTriangle, FileDown, PencilLine, RefreshCcw, Save, Share2, Sparkles, Trash2, UsersRound } from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import AppLayout from "../components/AppLayout";
import Button from "../components/Button";
import DrillDownControls from "../components/DrillDownControls";
import Loading from "../components/Loading";
import ProfileAvatar from "../components/ProfileAvatar";

import {
  generateDashboard,
  getDashboard,
  getDashboards,
  deleteDashboard,
  saveChartSettings,
  refreshDashboard,
} from "../api/dashboardApi";
import { getDataSources } from "../api/dataSourceApi";

import { getToken } from "../utils/storage";
import { aggregateDrillRows, canDrillDeeper, getDrillConfig } from "../utils/drillDown";
import {
  saveCreatedDashboardHandoff,
  takeCreatedDashboardHandoff,
} from "../utils/dashboardHandoff";
import { deleteCollaboration, getDashboardAccess } from "../api/collaborationApi";

const DEFAULT_PIE_COLORS = [
  "#4f46e5",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#84cc16",
  "#f97316",
  "#14b8a6",
  "#64748b",
  "#0ea5e9",
];

const DEFAULT_CHART_SETTINGS = {
  chartColor: "#4f46e5",
  chartBackground: "#f8fafc",
  xAxisTextColor: "#0f172a",
  yAxisTextColor: "#0f172a",
  gridColor: "#cbd5e1",
  gridStyle: "3 3",
  barStyle: "rounded",
  pieColors: DEFAULT_PIE_COLORS,
  showLegend: true,
};

export default function Dashboards() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [dashboards, setDashboards] = useState([]);
  const [selectedDashboard, setSelectedDashboard] = useState(null);

  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [dataSources, setDataSources] = useState([]);
  const [selectedDataSourceId, setSelectedDataSourceId] = useState("");
  const [generationStatus, setGenerationStatus] = useState("");

  const [chartSettings, setChartSettings] = useState({});
  const [drillStates, setDrillStates] = useState({});

  const [showDeleteDashboardModal, setShowDeleteDashboardModal] = useState(false);
  const [dashboardToDelete, setDashboardToDelete] = useState(null);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [showPromptConfirmation, setShowPromptConfirmation] = useState(false);
  const [dashboardPrompt, setDashboardPrompt] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [refreshingDashboard, setRefreshingDashboard] = useState(false);
  const [error, setError] = useState("");
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [dashboardAccess, setDashboardAccess] = useState([]);

  const charts = selectedDashboard?.charts || [];
  const accessPermission = selectedDashboard?.access_permission || "owner";
  const canEditDashboard = accessPermission !== "read";
  const canRefreshDashboard = accessPermission === "owner" || accessPermission === "full";

  async function openAccessModal() {
    try {
      const response = await getDashboardAccess(getToken(), selectedDashboard.id);
      setDashboardAccess(response?.collaborators || []);
      setShowAccessModal(true);
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function leaveSharedDashboard() {
    try {
      await deleteCollaboration(getToken(), selectedDashboard.collaboration_id);
      toast.success("Compartilhamento removido.");
      navigate("/home");
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function loadDashboards(options = {}) {
    setLoadingList(true);
    setError("");

    try {
      const token = getToken();
      const response = await getDashboards(token);
      const dashboardList = response?.dashboards || [];

      setDashboards(dashboardList);

      if (options.skipOpen) {
        return;
      }

      const dashboardIdFromUrl = options.dashboardId || searchParams.get("dashboard_id");

      if (dashboardIdFromUrl) {
        await openDashboard(dashboardIdFromUrl);
        return;
      }

      if (!selectedDashboard && dashboardList.length > 0) {
        await openDashboard(dashboardList[0].id);
      }
    } catch (err) {
      setError(err.message || "Erro ao buscar dashboards.");
    } finally {
      setLoadingList(false);
    }
  }

  async function openDashboard(dashboardId) {
    setError("");

    try {
      const token = getToken();
      const response = await getDashboard(token, dashboardId);
      setSelectedDashboard(response?.dashboard || null);
    } catch (err) {
      setError(err.message || "Erro ao abrir dashboard.");
    }
  }

  function getChartId(chart, index) {
    return String(chart?.id || chart?.chart_id || `chart_${index}`);
  }

  function normalizePieColors(value) {
    if (Array.isArray(value)) {
      return value.length ? value : DEFAULT_PIE_COLORS;
    }

    if (typeof value === "string" && value.trim()) {
      try {
        const parsed = JSON.parse(value);

        if (Array.isArray(parsed) && parsed.length) {
          return parsed;
        }
      } catch {
        const colors = value
          .split(",")
          .map((color) => color.trim())
          .filter(Boolean);

        if (colors.length) {
          return colors;
        }
      }
    }

    return DEFAULT_PIE_COLORS;
  }

  function normalizeSettings(settings = {}) {
    return {
      chartColor: settings.chart_color || settings.chartColor || DEFAULT_CHART_SETTINGS.chartColor,
      chartBackground: settings.chart_background || settings.chartBackground || DEFAULT_CHART_SETTINGS.chartBackground,
      xAxisTextColor: settings.x_axis_text_color || settings.xAxisTextColor || DEFAULT_CHART_SETTINGS.xAxisTextColor,
      yAxisTextColor: settings.y_axis_text_color || settings.yAxisTextColor || DEFAULT_CHART_SETTINGS.yAxisTextColor,
      gridColor: settings.grid_color || settings.gridColor || DEFAULT_CHART_SETTINGS.gridColor,
      gridStyle: settings.grid_style || settings.gridStyle || DEFAULT_CHART_SETTINGS.gridStyle,
      barStyle: settings.bar_style || settings.barStyle || DEFAULT_CHART_SETTINGS.barStyle,
      pieColors: normalizePieColors(settings.pie_colors || settings.pieColors),
      showLegend: settings.show_legend ?? settings.showLegend ?? DEFAULT_CHART_SETTINGS.showLegend,
    };
  }

  function getPieColor(settings, index) {
    const colors = normalizePieColors(settings.pieColors);
    return colors[index % colors.length] || DEFAULT_PIE_COLORS[index % DEFAULT_PIE_COLORS.length];
  }

  function updatePieSliceColor(chartId, index, value) {
    setChartSettings((prev) => {
      const currentSettings = {
        ...DEFAULT_CHART_SETTINGS,
        ...(prev[chartId] || {}),
      };

      const nextColors = [...normalizePieColors(currentSettings.pieColors)];
      nextColors[index] = value;

      return {
        ...prev,
        [chartId]: {
          ...currentSettings,
          pieColors: nextColors,
        },
      };
    });
  }

  function updateChartSetting(chartId, key, value) {
    setChartSettings((prev) => ({
      ...prev,
      [chartId]: {
        ...DEFAULT_CHART_SETTINGS,
        ...(prev[chartId] || {}),
        [key]: value,
      },
    }));
  }

  function getDrillPath(chartId) {
    return drillStates[chartId]?.path || [];
  }

  function drillInto(chartId, column, value) {
    if (!column || value === null || value === undefined) return;

    setDrillStates((prev) => {
      const currentPath = prev[chartId]?.path || [];

      return {
        ...prev,
        [chartId]: {
          path: [
            ...currentPath,
            {
              column,
              value: String(value),
            },
          ],
        },
      };
    });
  }

  function drillUp(chartId) {
    setDrillStates((prev) => {
      const currentPath = prev[chartId]?.path || [];

      return {
        ...prev,
        [chartId]: {
          path: currentPath.slice(0, -1),
        },
      };
    });
  }

  function resetDrill(chartId, depth = 0) {
    setDrillStates((prev) => {
      const currentPath = prev[chartId]?.path || [];

      return {
        ...prev,
        [chartId]: {
          path: currentPath.slice(0, depth),
        },
      };
    });
  }

  async function handleSaveChartSettings() {
    if (!selectedDashboard?.id) {
      setError("Nenhum dashboard selecionado.");
      toast.error("Nenhum dashboard selecionado.");
      return;
    }

    if (!charts.length) {
      setError("Nenhum gráfico encontrado.");
      toast.error("Nenhum gráfico encontrado.");
      return;
    }

    try {
      setSavingSettings(true);
      setError("");

      const token = getToken();

      await Promise.all(
        charts.map((chart, index) => {
          const chartId = getChartId(chart, index);
          const settings = chartSettings[chartId] || DEFAULT_CHART_SETTINGS;
          const realChartId = chart?.id || chart?.chart_id;

          return saveChartSettings({
            token,
            dashboard_id: selectedDashboard.id,
            chart_id: realChartId,
            chart_color: settings.chartColor,
            chart_background: settings.chartBackground,
            x_axis_text_color: settings.xAxisTextColor,
            y_axis_text_color: settings.yAxisTextColor,
            grid_color: settings.gridColor,
            grid_style: settings.gridStyle,
            bar_style: settings.barStyle,
            pie_colors: normalizePieColors(settings.pieColors),
            show_legend: settings.showLegend,
          });
        })
      );

      toast.success("Configurações de todos os gráficos salvas.");
    } catch (err) {
      const message = err.message || "Erro ao salvar configurações.";
      setError(message);
      toast.error(message);
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleExportPdf() {
    try {
      setExportingPdf(true);
      setError("");

      const element = document.getElementById("dashboard-export-area");

      if (!element) {
        setError("Área de exportação não encontrada.");
        toast.error("Área de exportação não encontrada.");
        return;
      }

      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });

      const imgData = canvas.toDataURL("image/png");

      const pdf = new jsPDF({
        orientation: "landscape",
        unit: "px",
        format: [canvas.width, canvas.height],
      });

      pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);
      pdf.save(`${selectedDashboard?.title || "dashboard"}.pdf`);

      toast.success("PDF exportado com sucesso.");
    } catch {
      setError("Erro ao exportar PDF.");
      toast.error("Erro ao exportar PDF.");
    } finally {
      setExportingPdf(false);
    }
  }

  async function refreshSelectedDashboard(promptOverride) {
    if (!selectedDashboard?.id) {
      setError("Nenhum dashboard selecionado.");
      toast.error("Nenhum dashboard selecionado.");
      return;
    }

    if (!selectedDashboard?.data_source_id) {
      setError("Este dashboard não está ligado a uma fonte de dados.");
      toast.error("Este dashboard não está ligado a uma fonte de dados.");
      return;
    }

    try {
      setRefreshingDashboard(true);
      setError("");

      const token = getToken();

      const response = await refreshDashboard({
        token,
        dashboard: selectedDashboard,
        prompt: promptOverride,
      });

      const refreshedDashboard =
        response?.dashboard ||
        response;

      if (refreshedDashboard?.id) {
        await openDashboard(refreshedDashboard.id);
      } else {
        await openDashboard(selectedDashboard.id);
      }

      await loadDashboards();

      toast.success("Dashboard atualizado com sucesso.");
    } catch (err) {
      console.error("Erro ao atualizar dashboard:", err);

      setError(err.message || "Erro ao atualizar dashboard.");
      toast.error(err.message || "Erro ao atualizar dashboard.");
    } finally {
      setRefreshingDashboard(false);
    }
  }

  async function loadDashboardSources() {
    try {
      const response = await getDataSources(getToken());
      const sources = response?.data_sources || [];

      setDataSources(sources);

      if (!selectedDataSourceId && sources[0]?.id) {
        setSelectedDataSourceId(String(sources[0].id));
      }
    } catch (err) {
      toast.error(err.message || "Erro ao buscar fontes de dados.");
    }
  }

  function handleRefreshDashboard() {
    refreshSelectedDashboard();
  }

  function openPromptModal() {
    if (!selectedDashboard?.data_source_id) {
      setError("Este dashboard não está ligado a uma fonte de dados.");
      toast.error("Este dashboard não está ligado a uma fonte de dados.");
      return;
    }

    setDashboardPrompt(selectedDashboard.prompt || "");
    setShowPromptConfirmation(false);
    setShowPromptModal(true);
  }

  function closePromptModal() {
    if (refreshingDashboard) return;

    setShowPromptModal(false);
    setShowPromptConfirmation(false);
    setDashboardPrompt("");
  }

  function requestPromptUpdate(event) {
    event.preventDefault();

    if (!dashboardPrompt.trim()) {
      setError("Digite um prompt para refazer a análise.");
      toast.error("Digite um prompt para refazer a análise.");
      return;
    }

    setError("");
    setShowPromptModal(false);
    setShowPromptConfirmation(true);
  }

  async function confirmPromptUpdate() {
    const nextPrompt = dashboardPrompt.trim();

    setShowPromptConfirmation(false);

    await refreshSelectedDashboard(nextPrompt);

    setDashboardPrompt("");
  }

  async function handleGenerate(event) {
    event.preventDefault();

    if (!title.trim()) return setError("Digite o nome do dashboard.");
    if (!selectedDataSourceId) return setError("Escolha uma fonte de dados.");

    setLoading(true);
    setGenerationStatus("Preparando a geracao do dashboard...");
    setError("");

    try {
      const token = getToken();

      const response = await generateDashboard({
        token,
        title: title.trim(),
        prompt: prompt.trim(),
        data_source_id: selectedDataSourceId,
        onStatus: setGenerationStatus,
      });

      const createdDashboardId = response?.dashboard?.id || response?.id;

      if (!createdDashboardId) {
        throw new Error("A API respondeu, mas nao retornou o dashboard criado.");
      }

      setGenerationStatus("Abrindo dashboard gerado.");

      if (response?.dashboard) {
        const createdDashboard = {
          ...response.dashboard,
          charts: response.dashboard.charts || response.charts || [],
        };

        setSelectedDashboard(createdDashboard);
        setDashboards((prev) => [
          createdDashboard,
          ...prev.filter(
            (dashboard) => Number(dashboard.id) !== Number(createdDashboard.id)
          ),
        ]);
      }

      saveCreatedDashboardHandoff(response);
      setShowCreate(false);
      setTitle("");
      setPrompt("");
      setSelectedDataSourceId("");
      setGenerationStatus("");
      navigate(`/dashboards?dashboard_id=${createdDashboardId}`);
      loadDashboards({ skipOpen: true });
    } catch (err) {
      console.error("Erro ao gerar dashboard:", err);

      setError(err.message || "Erro ao gerar dashboard.");
      toast.error(err.message || "Erro ao gerar dashboard.");
    } finally {
      setLoading(false);
      setGenerationStatus("");
    }
  }

  function cancelDeleteDashboard() {
    if (loadingDelete) return;

    setDashboardToDelete(null);
    setShowDeleteDashboardModal(false);
  }

  async function confirmDeleteDashboard() {
    setLoadingDelete(true);
    setError("");

    try {
      const token = getToken();

      await deleteDashboard(token, dashboardToDelete);

      setDashboards((prev) =>
        prev.filter((dashboard) => Number(dashboard.id) !== Number(dashboardToDelete))
      );

      if (Number(selectedDashboard?.id) === Number(dashboardToDelete)) {
        setSelectedDashboard(null);
      }

      setDashboardToDelete(null);
      setShowDeleteDashboardModal(false);

      toast.success("Dashboard excluído com sucesso.");
    } catch (err) {
      const message = err.message || "Erro ao deletar dashboard.";
      setError(message);
      toast.error(message);
    } finally {
      setLoadingDelete(false);
    }
  }

  function getRawChartData(currentChart) {
    if (!currentChart) return [];
    if (Array.isArray(currentChart.chart_data?.data)) return currentChart.chart_data.data;
    if (Array.isArray(currentChart.chart_data)) return currentChart.chart_data;
    if (Array.isArray(currentChart.data)) return currentChart.data;
    return [];
  }

  function normalizeKey(key) {
    if (!key) return "";

    return String(key)
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "_");
  }

  function formatDisplayText(value) {
    return String(value ?? "")
      .replace(/_/g, " ")
      .replace(/-/g, " ")
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .replace(/\s+/g, " ")
      .trim();
  }

  function formatColumnLabel(value) {
    const text = formatDisplayText(value);

    if (!text) return "";

    const special = {
      id: "ID",
      cpf: "CPF",
      cnpj: "CNPJ",
      cep: "CEP",
      qtd: "Quantidade",
      qtde: "Quantidade",
      rh: "RH",
      roi: "ROI",
      ctr: "CTR",
      cpc: "CPC",
      cpa: "CPA",
      sla: "SLA",
    };

    return text
      .split(" ")
      .map((word) => {
        const normalized = normalizeKey(word);
        return special[normalized] || `${word.slice(0, 1).toUpperCase()}${word.slice(1).toLowerCase()}`;
      })
      .join(" ");
  }

  function findRealKey(data, wantedKey) {
    const firstItem = data?.[0] || {};
    const keys = Object.keys(firstItem);

    if (!wantedKey || keys.length === 0) return null;

    const exactKey = keys.find((key) => key === wantedKey);
    if (exactKey) return exactKey;

    const normalizedWanted = normalizeKey(wantedKey);

    return (
      keys.find((key) => normalizeKey(key) === normalizedWanted) ||
      keys.find((key) => normalizeKey(key).includes(normalizedWanted)) ||
      null
    );
  }

  function isNumericLike(value) {
    if (value === null || value === undefined || value === "") return false;
    if (typeof value === "number") return !Number.isNaN(value);

    const normalized = String(value)
      .trim()
      .replace(/\./g, "")
      .replace(",", ".");

    return normalized !== "" && !Number.isNaN(Number(normalized));
  }

  function isMostlyNumeric(data, key) {
    if (!key) return false;

    const sample = data
      .slice(0, 12)
      .map((item) => item?.[key])
      .filter((value) => value !== null && value !== undefined && value !== "");

    if (sample.length === 0) return false;

    const numericCount = sample.filter(isNumericLike).length;

    return numericCount / sample.length >= 0.7;
  }

  function findCategoryKey(data, preferredKey, numericKey = null) {
    const firstItem = data?.[0] || {};
    const keys = Object.keys(firstItem);

    const realPreferredKey = findRealKey(data, preferredKey);

    if (realPreferredKey && realPreferredKey !== numericKey) {
      return realPreferredKey;
    }

    return (
      keys.find((key) => key !== numericKey && !isMostlyNumeric(data, key)) ||
      keys.find((key) => key !== numericKey) ||
      realPreferredKey ||
      keys[0] ||
      null
    );
  }

  function findNumericKey(data, preferredKey, categoryKey = null, allowFallback = true) {
    const firstItem = data?.[0] || {};
    const keys = Object.keys(firstItem);

    const realPreferredKey = findRealKey(data, preferredKey);

    if (
      realPreferredKey &&
      realPreferredKey !== categoryKey &&
      isMostlyNumeric(data, realPreferredKey)
    ) {
      return realPreferredKey;
    }

    if (!allowFallback) {
      return null;
    }

    return (
      keys.find((key) => key !== categoryKey && isMostlyNumeric(data, key)) ||
      keys.find((key) => key !== categoryKey) ||
      realPreferredKey ||
      null
    );
  }

  function getMetricConfig(currentChart) {
    const metric = currentChart?.metric;
    const firstMetric = Array.isArray(metric) ? metric[0] : metric;

    return (
      currentChart?.chart_config?.y ||
      currentChart?.config?.y ||
      currentChart?.y ||
      currentChart?.yKey ||
      firstMetric
    );
  }

  function getXAxisConfig(currentChart) {
    return (
      currentChart?.chart_config?.x ||
      currentChart?.config?.x ||
      currentChart?.x ||
      currentChart?.xKey ||
      currentChart?.time_column ||
      currentChart?.group_by?.[0]
    );
  }

  function looksLikeDateKey(key) {
    const normalized = normalizeKey(key);

    return (
      normalized.includes("data") ||
      normalized.includes("date") ||
      normalized.includes("dia") ||
      normalized.includes("mes") ||
      normalized.includes("ano") ||
      normalized.includes("periodo")
    );
  }

  function titleMentionsMetric(title, metricKey) {
    if (!title || !metricKey) return false;

    const normalizedTitle = normalizeKey(title);
    const normalizedMetric = normalizeKey(metricKey);

    if (normalizedTitle.includes(normalizedMetric)) return true;

    const aliases = {
      cliques: ["clique", "cliques", "click", "clicks"],
      impressoes: ["impressao", "impressoes", "impression", "impressions"],
      conversoes: ["conversao", "conversoes", "conversion", "conversions"],
      receita: ["receita", "faturamento", "revenue"],
      investimento: ["investimento", "gasto", "custo", "spend", "cost"],
      vendas: ["venda", "vendas", "sales"],
      quantidade: ["quantidade", "qtd", "volume"],
    };

    return Object.values(aliases).some((group) => {
      const metricMatchesGroup = group.some((alias) => normalizedMetric.includes(alias));
      const titleMatchesGroup = group.some((alias) => normalizedTitle.includes(alias));
      return metricMatchesGroup && titleMatchesGroup;
    });
  }

  function getChartKeys(data, currentChart) {
    const firstItem = data?.[0] || {};
    const keys = Object.keys(firstItem);

    if (keys.length === 0) {
      return { xKey: null, yKey: null };
    }

    const chartType = currentChart?.chart_type || currentChart?.type || "bar";
    const operation = currentChart?.operation;

    const configX = getXAxisConfig(currentChart);
    const configY = getMetricConfig(currentChart);

    if (chartType === "table" || operation === "table") {
      return {
        xKey: keys[0] || null,
        yKey: keys[1] || keys[0] || null,
      };
    }

    if (chartType === "scatter" || operation === "scatter") {
      const numericKeys = keys.filter((key) => isMostlyNumeric(data, key));

      let xKey = findRealKey(data, configX);
      let yKey = findRealKey(data, configY);

      if (!xKey || !isMostlyNumeric(data, xKey)) {
        xKey = numericKeys[0] || null;
      }

      if (!yKey || yKey === xKey || !isMostlyNumeric(data, yKey)) {
        yKey = numericKeys.find((key) => key !== xKey) || null;
      }

      return { xKey, yKey };
    }

    if (operation === "count" || configY === "count") {
      const yKey =
        findRealKey(data, "count") ||
        findRealKey(data, "quantidade") ||
        findRealKey(data, "total") ||
        findRealKey(data, "qtd") ||
        keys.find((key) => normalizeKey(key) === "count") ||
        keys.find((key) => normalizeKey(key) === "quantidade") ||
        keys.find((key) => normalizeKey(key) === "total") ||
        keys.find((key) => normalizeKey(key) === "qtd") ||
        keys.find((key) => normalizeKey(key).includes("quantidade")) ||
        keys.find((key) => normalizeKey(key).includes("total")) ||
        keys.find((key) => isMostlyNumeric(data, key)) ||
        null;

      const xKey = findCategoryKey(data, configX, yKey);

      return { xKey, yKey };
    }

    let yKey = findNumericKey(data, configY, null, true);
    let xKey = findCategoryKey(data, configX, yKey);

    if (chartType === "horizontal_bar") {
      const explicitY = findNumericKey(data, configY, null, false);

      if (explicitY) {
        yKey = explicitY;
      }

      xKey = findCategoryKey(data, configX, yKey);
    }

    const title = currentChart?.title || "";

    if (
      yKey &&
      title &&
      !titleMentionsMetric(title, yKey) &&
      keys.some((key) => isMostlyNumeric(data, key) && titleMentionsMetric(title, key))
    ) {
      const titleMetricKey = keys.find(
        (key) => isMostlyNumeric(data, key) && titleMentionsMetric(title, key)
      );

      if (titleMetricKey) {
        yKey = titleMetricKey;
      }
    }

    if (xKey && yKey && xKey === yKey) {
      xKey =
        keys.find((key) => key !== yKey && !isMostlyNumeric(data, key)) ||
        keys.find((key) => key !== yKey) ||
        null;
    }

    if (!xKey && operation === "time_groupby") {
      xKey = keys.find(looksLikeDateKey) || findCategoryKey(data, configX, yKey);
    }

    return { xKey, yKey };
  }

  function parseNumericValue(value) {
    if (typeof value === "number") return value;

    const normalized = String(value ?? "")
      .trim()
      .replace(/\./g, "")
      .replace(",", ".");

    const parsed = Number(normalized);

    return Number.isNaN(parsed) ? 0 : parsed;
  }

  function formatChartData(data, yKey) {
    if (!yKey) return data;

    return data.map((item) => ({
      ...item,
      [yKey]: parseNumericValue(item[yKey]),
    }));
  }

  function formatTooltipValue(value) {
    if (typeof value === "number") {
      return value.toLocaleString("pt-BR", {
        maximumFractionDigits: 2,
      });
    }

    return String(value ?? "");
  }

  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || payload.length === 0) return null;

    return (
      <div className="custom-chart-tooltip">
        <strong>{label}</strong>

        {payload.map((item, index) => (
          <p key={`${item.name}-${index}`}>
            {formatColumnLabel(item.name)}: {formatTooltipValue(item.value)}
          </p>
        ))}
      </div>
    );
  }

  useEffect(() => {
    const dashboardIdFromUrl = searchParams.get("dashboard_id");
    const createdDashboard = takeCreatedDashboardHandoff(dashboardIdFromUrl);

    if (createdDashboard) {
      setSelectedDashboard(createdDashboard);
    }

    loadDashboards({ dashboardId: dashboardIdFromUrl });
  }, [searchParams]);

  useEffect(() => {
    if (showCreate) {
      loadDashboardSources();
    }
  }, [showCreate]);

  useEffect(() => {
    if (!selectedDashboard) {
      setChartSettings({});
      setDrillStates({});
      return;
    }

    const dashboardDefaults = normalizeSettings(selectedDashboard.chart_settings || {});
    const nextSettings = {};

    (selectedDashboard.charts || []).forEach((currentChart, index) => {
      const chartId = getChartId(currentChart, index);

      nextSettings[chartId] = normalizeSettings({
        ...dashboardDefaults,
        ...(currentChart.chart_settings || {}),
      });
    });

    setChartSettings(nextSettings);
    setDrillStates({});
  }, [selectedDashboard]);

  function getBarRadius(barStyle) {
    if (barStyle === "square") return [0, 0, 0, 0];
    if (barStyle === "soft") return [4, 4, 0, 0];
    return [10, 10, 0, 0];
  }

  function getBarSize(barStyle) {
    if (barStyle === "thin") return 42;
    if (barStyle === "thick") return 100;
    return 76;
  }

  function renderCustomXAxisTick(props, settings) {
    const { x, y, payload } = props;

    return (
      <text
        x={x}
        y={y + 12}
        fill={settings.xAxisTextColor}
        fontSize={12}
        fontWeight={700}
        textAnchor="end"
        transform={`rotate(-30, ${x}, ${y})`}
      >
        {payload.value}
      </text>
    );
  }

  function renderCustomYAxisTick(props, settings) {
    const { x, y, payload } = props;

    return (
      <text
        x={x - 8}
        y={y + 4}
        fill={settings.yAxisTextColor}
        fontSize={12}
        fontWeight={700}
        textAnchor="end"
      >
        {payload.value}
      </text>
    );
  }

  function renderXAxis(xKey, settings) {
    return (
      <XAxis
        dataKey={xKey}
        interval={0}
        height={115}
        tick={(props) => renderCustomXAxisTick(props, settings)}
        axisLine={{ stroke: "#94a3b8" }}
        tickLine={{ stroke: "#94a3b8" }}
      />
    );
  }

  function renderYAxis(yKey, settings, withDataKey = false) {
    return (
      <YAxis
        dataKey={withDataKey ? yKey : undefined}
        tick={(props) => renderCustomYAxisTick(props, settings)}
        axisLine={{ stroke: "#94a3b8" }}
        tickLine={{ stroke: "#94a3b8" }}
      />
    );
  }

  function renderGrid(settings) {
    return <CartesianGrid strokeDasharray={settings.gridStyle} stroke={settings.gridColor} />;
  }

  function renderChart(currentChart, settings, chartId) {
    const rawChartData = getRawChartData(currentChart);
    const chartType = currentChart?.chart_type || currentChart?.type || "bar";
    const operation = currentChart?.operation;
    const chartConfig = currentChart?.chart_config || currentChart?.config || {};

    const { xKey, yKey } = getChartKeys(rawChartData, currentChart);
    const drillConfig = getDrillConfig(currentChart, rawChartData, xKey);
    const drillPath = getDrillPath(chartId);
    const drillEnabled = drillConfig.enabled && drillConfig.hierarchy.length > 1;
    const drillLevel = Math.min(drillPath.length, Math.max(drillConfig.hierarchy.length - 1, 0));
    const drillXKey = drillEnabled ? drillConfig.hierarchy[drillLevel]?.column : xKey;
    const isCountChart = operation === "count" || chartConfig.operation === "count" || chartConfig.aggregation === "count";
    const drillMeta = chartConfig.drill_down || currentChart?.drill_down || {};
    const sourceYKey = drillMeta.metric_column || yKey;
    const drillYKey = drillEnabled && isCountChart ? "Quantidade" : yKey;
    const aggregation = currentChart?.aggregation || chartConfig.aggregation || "sum";
    const chartData = formatChartData(
      drillEnabled
        ? aggregateDrillRows({
            rows: drillConfig.rows,
            hierarchy: drillConfig.hierarchy,
            path: drillPath,
            yKey: drillYKey,
            sourceYKey: isCountChart ? null : sourceYKey,
            aggregation,
            operation,
            limit: currentChart?.limit || chartConfig.limit || 20,
            sort: currentChart?.sort || chartConfig.sort || "desc",
          })
        : rawChartData,
      drillYKey
    );
    const activeXKey = drillEnabled ? drillXKey : xKey;
    const activeYKey = drillEnabled ? drillYKey : yKey;
    const canGoDeeper = drillEnabled && canDrillDeeper(drillConfig.hierarchy, drillPath);

    function handleDrillClick(row) {
      if (!canGoDeeper || !row || !activeXKey) return;

      drillInto(chartId, activeXKey, row[activeXKey]);
    }

    if (!currentChart || chartData.length === 0) {
      return <p>Sem dados para exibir.</p>;
    }

    if (chartType !== "table" && (!activeXKey || !activeYKey)) {
      console.log("Gráfico com configuração incompleta:", {
        currentChart,
        rawChartData,
        xKey: activeXKey,
        yKey: activeYKey,
      });

      return <p>Configuração do gráfico incompleta.</p>;
    }

    const chartWidth =
      chartType === "pie" || chartType === "donut"
        ? 1100
        : chartType === "horizontal_bar"
          ? 1200
          : Math.max(chartData.length * 140, 1200);

    const chartHeight =
      chartType === "horizontal_bar"
        ? Math.max(chartData.length * 58, 560)
        : 620;

    const chartWrapperStyle = {
      width: chartWidth,
      height: chartHeight,
      backgroundColor: settings.chartBackground,
      borderRadius: 20,
      padding: 24,
    };

    const drillControls = (
      <DrillDownControls
        hierarchy={drillConfig.hierarchy}
        path={drillPath}
        canGoBack={drillPath.length > 0}
        onBack={() => drillUp(chartId)}
        onReset={(depth) => resetDrill(chartId, typeof depth === "number" ? depth : 0)}
      />
    );

    if (chartType === "kpi" || operation === "kpi") {
      const value = chartData?.[0]?.[activeYKey];

      return (
        <div className="chart-scroll">
          <div style={chartWrapperStyle} className="dashboard-kpi-card">
            <span>{formatDisplayText(currentChart.title || formatColumnLabel(activeYKey))}</span>
            <strong>{formatTooltipValue(value)}</strong>
          </div>
        </div>
      );
    }

    if (chartType === "line") {
      return (
        <>
          {drillControls}
          <div className="chart-scroll">
            <div style={chartWrapperStyle}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 24, right: 55, left: 34, bottom: 96 }}
                  onClick={(event) => handleDrillClick(event?.activePayload?.[0]?.payload)}
                >
                  {renderGrid(settings)}
                  {renderXAxis(activeXKey, settings)}
                  {renderYAxis(activeYKey, settings)}
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey={activeYKey}
                    name={formatColumnLabel(activeYKey)}
                    stroke={settings.chartColor}
                    strokeWidth={4}
                    dot={{ r: 5, fill: settings.chartColor, cursor: canGoDeeper ? "pointer" : "default" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }

    if (chartType === "area") {
      return (
        <>
          {drillControls}
          <div className="chart-scroll">
            <div style={chartWrapperStyle}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 24, right: 55, left: 34, bottom: 96 }}
                  onClick={(event) => handleDrillClick(event?.activePayload?.[0]?.payload)}
                >
                  {renderGrid(settings)}
                  {renderXAxis(activeXKey, settings)}
                  {renderYAxis(activeYKey, settings)}
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey={activeYKey}
                    name={formatColumnLabel(activeYKey)}
                    stroke={settings.chartColor}
                    fill={settings.chartColor}
                    fillOpacity={0.24}
                    strokeWidth={4}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }

    if (chartType === "pie" || chartType === "donut") {
      return (
        <>
          {drillControls}
          <div className="chart-scroll">
            <div style={chartWrapperStyle}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Tooltip content={<CustomTooltip />} />

                  {settings.showLegend && (
                    <Legend
                      verticalAlign="bottom"
                      height={70}
                      wrapperStyle={{
                        color: settings.xAxisTextColor,
                        fontWeight: 700,
                        fontSize: 13,
                      }}
                    />
                  )}

                  <Pie
                    data={chartData}
                    dataKey={activeYKey}
                    nameKey={activeXKey}
                    innerRadius={chartType === "donut" ? 100 : 0}
                    outerRadius={220}
                    label
                    onClick={(row) => handleDrillClick(row)}
                    cursor={canGoDeeper ? "pointer" : "default"}
                  >
                    {chartData.map((_, index) => (
                      <Cell key={`slice-${index}`} fill={getPieColor(settings, index)} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }

    if (chartType === "scatter") {
      return (
        <>
          {drillControls}
          <div className="chart-scroll">
            <div style={chartWrapperStyle}>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart
                  margin={{ top: 24, right: 55, left: 34, bottom: 96 }}
                  onClick={(event) => handleDrillClick(event?.activePayload?.[0]?.payload)}
                >
                  {renderGrid(settings)}
                  {renderXAxis(activeXKey, settings)}
                  {renderYAxis(activeYKey, settings, true)}
                  <Tooltip content={<CustomTooltip />} />
                  <Scatter
                    data={chartData}
                    fill={settings.chartColor}
                    name={formatColumnLabel(activeYKey)}
                    onClick={(row) => handleDrillClick(row?.payload || row)}
                    cursor={canGoDeeper ? "pointer" : "default"}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }

    if (chartType === "horizontal_bar") {
      return (
        <>
          {drillControls}
          <div className="chart-scroll">
            <div style={chartWrapperStyle}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 24, right: 55, left: 160, bottom: 40 }}
                >
                  {renderGrid(settings)}

                  <XAxis
                    type="number"
                    tick={{
                      fill: settings.xAxisTextColor,
                      fontSize: 12,
                      fontWeight: 700,
                    }}
                    axisLine={{ stroke: "#94a3b8" }}
                    tickLine={{ stroke: "#94a3b8" }}
                  />

                  <YAxis
                    dataKey={activeXKey}
                    type="category"
                    width={165}
                    tick={{
                      fill: settings.yAxisTextColor,
                      fontSize: 12,
                      fontWeight: 700,
                    }}
                    axisLine={{ stroke: "#94a3b8" }}
                    tickLine={{ stroke: "#94a3b8" }}
                  />

                  <Tooltip content={<CustomTooltip />} />

                  <Bar
                    dataKey={activeYKey}
                    name={formatColumnLabel(activeYKey)}
                    fill={settings.chartColor}
                    radius={[0, 10, 10, 0]}
                    barSize={Math.min(getBarSize(settings.barStyle), 46)}
                    minPointSize={4}
                    onClick={(row) => handleDrillClick(row?.payload || row)}
                    cursor={canGoDeeper ? "pointer" : "default"}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }

    if (chartType === "table") {
      return (
        <div className="chart-scroll">
          <div className="dashboard-table-chart">
            <table>
              <thead>
                <tr>
                  {Object.keys(chartData[0] || {}).map((key) => (
                    <th key={key}>{formatColumnLabel(key)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {chartData.map((row, index) => (
                  <tr key={index}>
                    {Object.keys(chartData[0] || {}).map((key) => (
                      <td key={key}>{String(row[key])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    return (
      <>
        {drillControls}
        <div className="chart-scroll">
          <div style={chartWrapperStyle}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 24, right: 55, left: 34, bottom: 96 }} barCategoryGap="20%">
                {renderGrid(settings)}
                {renderXAxis(activeXKey, settings)}
                {renderYAxis(activeYKey, settings)}
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey={activeYKey}
                  name={formatColumnLabel(activeYKey)}
                  fill={settings.chartColor}
                  radius={getBarRadius(settings.barStyle)}
                  barSize={getBarSize(settings.barStyle)}
                  minPointSize={4}
                  onClick={(row) => handleDrillClick(row?.payload || row)}
                  cursor={canGoDeeper ? "pointer" : "default"}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </>
    );
  }

  function renderChartControls(currentChart, index) {
    const chartId = getChartId(currentChart, index);
    const settings = chartSettings[chartId] || DEFAULT_CHART_SETTINGS;
    const chartType = currentChart?.chart_type || currentChart?.type || "bar";
    const rawChartData = getRawChartData(currentChart);
    const { xKey } = getChartKeys(rawChartData, currentChart);
    const chartData = rawChartData || [];
    const isPieLike = chartType === "pie" || chartType === "donut";
    const isBarLike = chartType === "bar" || chartType === "horizontal_bar";
    const isCartesian = ["bar", "horizontal_bar", "line", "area", "scatter"].includes(chartType);

    if (!canEditDashboard) {
      return <div className="dashboard-chart-top"><h3>{formatDisplayText(currentChart.title || `Gráfico ${index + 1}`)}</h3></div>;
    }

    return (
      <>
        <div className="dashboard-chart-top">
          <h3>{formatDisplayText(currentChart.title || `Gráfico ${index + 1}`)}</h3>

          <div className="chart-custom-actions">
            {!isPieLike && (
              <label className="chart-color-button">
                <span>Gráfico</span>
                <span className="chart-color-preview" style={{ backgroundColor: settings.chartColor }} />
                <input type="color" defaultValue={settings.chartColor} onBlur={(event) => updateChartSetting(chartId, "chartColor", event.target.value)} />
              </label>
            )}

            <label className="chart-color-button">
              <span>Fundo</span>
              <span className="chart-color-preview" style={{ backgroundColor: settings.chartBackground }} />
              <input type="color" defaultValue={settings.chartBackground} onBlur={(event) => updateChartSetting(chartId, "chartBackground", event.target.value)} />
            </label>

            {isCartesian && (
              <>
                <label className="chart-color-button">
                  <span>Texto X</span>
                  <span className="chart-color-preview" style={{ backgroundColor: settings.xAxisTextColor }} />
                  <input type="color" defaultValue={settings.xAxisTextColor} onBlur={(event) => updateChartSetting(chartId, "xAxisTextColor", event.target.value)} />
                </label>

                <label className="chart-color-button">
                  <span>Texto Y</span>
                  <span className="chart-color-preview" style={{ backgroundColor: settings.yAxisTextColor }} />
                  <input type="color" defaultValue={settings.yAxisTextColor} onBlur={(event) => updateChartSetting(chartId, "yAxisTextColor", event.target.value)} />
                </label>

                <label className="chart-color-button">
                  <span>Traços</span>
                  <span className="chart-color-preview" style={{ backgroundColor: settings.gridColor }} />
                  <input type="color" defaultValue={settings.gridColor} onBlur={(event) => updateChartSetting(chartId, "gridColor", event.target.value)} />
                </label>
              </>
            )}
          </div>
        </div>

        {isCartesian && (
          <div className="chart-style-panel">
            <label>
              Tipo dos traços
              <select value={settings.gridStyle} onChange={(event) => updateChartSetting(chartId, "gridStyle", event.target.value)}>
                <option value="3 3">Pontilhado</option>
                <option value="8 4">Tracejado</option>
                <option value="1 0">Linha sólida</option>
                <option value="1 8">Espaçado</option>
              </select>
            </label>

            {isBarLike && (
              <label>
                Estilo das barras
                <select value={settings.barStyle} onChange={(event) => updateChartSetting(chartId, "barStyle", event.target.value)}>
                  <option value="rounded">Arredondada</option>
                  <option value="soft">Levemente arredondada</option>
                  <option value="square">Quadrada</option>
                  <option value="thin">Fina</option>
                  <option value="thick">Grossa</option>
                </select>
              </label>
            )}
          </div>
        )}

        {isPieLike && (
          <div className="chart-style-panel chart-pie-settings-panel">
            <label className="chart-toggle-label">
              Legenda
              <select
                value={settings.showLegend ? "true" : "false"}
                onChange={(event) => updateChartSetting(chartId, "showLegend", event.target.value === "true")}
              >
                <option value="true">Mostrar</option>
                <option value="false">Ocultar</option>
              </select>
            </label>

            <div className="chart-slice-colors">
              <span>Cores das partes</span>

              <div className="chart-slice-color-grid">
                {chartData.map((row, sliceIndex) => {
                  const label = xKey ? String(row?.[xKey] ?? `Parte ${sliceIndex + 1}`) : `Parte ${sliceIndex + 1}`;

                  return (
                    <label className="chart-slice-color-item" key={`${chartId}-slice-${sliceIndex}`} title={label}>
                      <span>{label}</span>
                      <input
                        type="color"
                        value={getPieColor(settings, sliceIndex)}
                        onChange={(event) => updatePieSliceColor(chartId, sliceIndex, event.target.value)}
                      />
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <AppLayout>
      <main className="dashboards-page dashboards-page-full">
        <section className="dashboard-content dashboard-content-full">
          <div className="dashboard-scroll-area">
            {error && <p className="error-message">{error}</p>}

            {!selectedDashboard ? (
              <div className="dashboard-empty">
                <h2>Nenhum dashboard aberto</h2>

                {loadingList ? (
                  <Loading
                    label="Carregando dashboards"
                    description="Buscando suas análises mais recentes."
                  />
                ) : dashboards.length === 0 ? (
                  <p>Crie seu primeiro dashboard para visualizar uma análise.</p>
                ) : (
                  <p>Selecione um dashboard pela sidebar para visualizar.</p>
                )}

                <Button onClick={() => setShowCreate(true)}>Criar Dashboard</Button>
              </div>
            ) : (
              <div className="dashboard-view">
                {refreshingDashboard && (
                  <Loading
                    overlay
                    label="Reconstruindo dashboard"
                    description="A IA está recalculando os gráficos e preparando uma nova análise."
                  />
                )}

                <div className="dashboard-view-header">
                  <div>
                    <h2 className="dashboard-title-hidden">{selectedDashboard.title}</h2>
                    {selectedDashboard.is_shared && (
                      <div className="dashboard-creator-badge">
                        <ProfileAvatar
                          image={selectedDashboard.creator_profile_image}
                          name={selectedDashboard.creator_name}
                        />
                        <span>Criado por <strong>@{selectedDashboard.creator_username}</strong></span>
                      </div>
                    )}
                  </div>

                  <div className="dashboard-actions">
                    {accessPermission === "owner" && (
                      <button type="button" className="dashboard-action-button" onClick={() => navigate(`/collaborations?dashboard_id=${selectedDashboard.id}`)}>
                        <Share2 size={18} />
                        <span>Compartilhar</span>
                      </button>
                    )}

                    <button type="button" className="dashboard-action-button" onClick={openAccessModal}>
                      <UsersRound size={18} />
                      <span>Acessos</span>
                    </button>

                    {selectedDashboard.is_shared && (
                      <button type="button" className="dashboard-action-button" onClick={leaveSharedDashboard}>
                        <Trash2 size={18} />
                        <span>Remover acesso</span>
                      </button>
                    )}

                    <button
                      type="button"
                      className="dashboard-action-button save-chart-button"
                      onClick={handleSaveChartSettings}
                      disabled={savingSettings || refreshingDashboard || !canEditDashboard}
                    >
                      <Save size={18} />
                      <span>{savingSettings ? "Salvando..." : "Salvar"}</span>
                    </button>

                    <button
                      type="button"
                      className="dashboard-action-button prompt-chart-button"
                      onClick={openPromptModal}
                      disabled={refreshingDashboard || savingSettings || exportingPdf || !selectedDashboard?.data_source_id || !canRefreshDashboard}
                      title={
                        selectedDashboard?.data_source_id
                          ? "Alterar o prompt e refazer toda a análise"
                          : "Este dashboard não está ligado a uma fonte de dados"
                      }
                    >
                      <PencilLine size={18} />
                      <span>Atualizar prompt</span>
                    </button>

                    <button
                      type="button"
                      className="dashboard-action-button refresh-chart-button"
                      onClick={handleRefreshDashboard}
                      disabled={refreshingDashboard || savingSettings || exportingPdf || !selectedDashboard?.data_source_id || !canRefreshDashboard}
                      title={
                        selectedDashboard?.data_source_id
                          ? "Atualizar dashboard usando a fonte de dados atual"
                          : "Este dashboard não está ligado a uma fonte de dados"
                      }
                    >
                      <RefreshCcw size={18} />
                      <span>{refreshingDashboard ? "Atualizando..." : "Atualizar"}</span>
                    </button>

                    <button
                      type="button"
                      className="dashboard-action-button export-chart-button"
                      onClick={handleExportPdf}
                      disabled={exportingPdf || refreshingDashboard}
                    >
                      <FileDown size={18} />
                      <span>{exportingPdf ? "Exportando..." : "Exportar"}</span>
                    </button>
                  </div>
                </div>

                {charts.length > 0 ? (
                  <>
                    <div id="dashboard-export-area" className="dashboard-chart-list">
                      {charts.map((currentChart, index) => {
                        const chartId = getChartId(currentChart, index);
                        const settings = chartSettings[chartId] || DEFAULT_CHART_SETTINGS;

                        return (
                          <div key={chartId} className="dashboard-chart-card dashboard-chart-card-large">
                            {renderChartControls(currentChart, index)}

                            <div className="dashboard-chart-real">
                              {renderChart(currentChart, settings, chartId)}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="dashboard-analysis-card">
                      <h3>Análise da IA</h3>
                      <ReactMarkdown>
                        {selectedDashboard.ai_suggestion || "Sem análise disponível."}
                      </ReactMarkdown>
                    </div>
                  </>
                ) : (
                  <p>Nenhum gráfico encontrado.</p>
                )}
              </div>
            )}
          </div>

          {showCreate && (
            <div className="modal-overlay">
              <form className="delete-modal-card" onSubmit={handleGenerate}>
                <h2>Criar Dashboard</h2>

                <label className="settings-label">
                  Nome do dashboard
                  <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ex: Vendas" />
                </label>

                <label className="settings-label">
                  Prompt da análise
                  <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ex: Analise os produtos mais vendidos" />
                </label>

                <label className="settings-label">
                  Fonte de dados
                  <select
                    value={selectedDataSourceId}
                    onChange={(event) => setSelectedDataSourceId(event.target.value)}
                  >
                    <option value="">Selecione uma fonte</option>
                    {dataSources.map((source) => (
                      <option key={source.id} value={source.id}>
                        {source.name} - {source.file_name}
                      </option>
                    ))}
                  </select>
                </label>

                {dataSources.length === 0 && (
                  <p className="dashboard-source-empty">
                    Cadastre uma fonte de dados antes de gerar dashboards.
                  </p>
                )}

                {generationStatus && (
                  <p className="dashboard-stream-status">{generationStatus}</p>
                )}

                <div className="delete-modal-actions">
                  <button type="button" className="modal-cancel" onClick={() => setShowCreate(false)} disabled={loading}>
                    Cancelar
                  </button>

                  <button type="submit" className="modal-confirm" disabled={loading}>
                    {loading ? "Gerando..." : "Gerar Dashboard"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {showPromptModal && (
            <div className="modal-overlay">
              <form className="prompt-update-modal" onSubmit={requestPromptUpdate}>
                <div className="prompt-update-modal-header">
                  <div className="prompt-update-icon">
                    <Sparkles size={22} />
                  </div>

                  <div>
                    <span className="prompt-update-kicker">Nova direção para a IA</span>
                    <h2>Atualizar prompt</h2>
                  </div>
                </div>

                <p>
                  Descreva o que você deseja analisar. A IA usará este novo
                  prompt para reconstruir o dashboard.
                </p>

                <label className="prompt-update-field">
                  Novo prompt
                  <textarea
                    value={dashboardPrompt}
                    onChange={(event) => setDashboardPrompt(event.target.value)}
                    placeholder="Ex: Compare o desempenho mensal por categoria e destaque os produtos com maior crescimento."
                    autoFocus
                  />
                  <small>{dashboardPrompt.trim().length} caracteres</small>
                </label>

                <div className="prompt-update-actions">
                  <button type="button" className="modal-cancel" onClick={closePromptModal}>
                    Cancelar
                  </button>

                  <button type="submit" className="prompt-update-primary">
                    Continuar
                  </button>
                </div>
              </form>
            </div>
          )}

          {showPromptConfirmation && (
            <div className="modal-overlay">
              <div className="prompt-confirmation-modal">
                <div className="prompt-warning-icon">
                  <AlertTriangle size={24} />
                </div>

                <div>
                  <span className="prompt-update-kicker">Confirme a atualização</span>
                  <h2>Refazer toda a análise?</h2>
                </div>

                <p>
                  O prompt atual será substituído. Todos os gráficos e a análise
                  textual deste dashboard serão gerados novamente com base no
                  novo pedido.
                </p>

                <div className="prompt-preview">
                  <span>Novo prompt</span>
                  <strong>{dashboardPrompt.trim()}</strong>
                </div>

                <div className="prompt-update-actions">
                  <button
                    type="button"
                    className="modal-cancel"
                    onClick={() => {
                      setShowPromptConfirmation(false);
                      setShowPromptModal(true);
                    }}
                    disabled={refreshingDashboard}
                  >
                    Voltar
                  </button>

                  <button
                    type="button"
                    className="prompt-confirm-button"
                    onClick={confirmPromptUpdate}
                    disabled={refreshingDashboard}
                  >
                    <RefreshCcw size={17} />
                    {refreshingDashboard ? "Atualizando..." : "Sim, refazer dashboard"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {showDeleteDashboardModal && (
            <div className="modal-overlay">
              <div className="delete-modal-card">
                <h2>Excluir dashboard</h2>
                <p>Tem certeza que deseja excluir este dashboard?</p>

                <div className="delete-modal-actions">
                  <button type="button" className="modal-cancel" onClick={cancelDeleteDashboard} disabled={loadingDelete}>
                    Cancelar
                  </button>

                  <button type="button" className="delete-confirm-button" onClick={confirmDeleteDashboard} disabled={loadingDelete}>
                    {loadingDelete ? "Excluindo..." : "Excluir"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {showAccessModal && (
            <div className="modal-overlay" onClick={() => setShowAccessModal(false)}>
              <div className="modal-card notification-modal" onClick={(event) => event.stopPropagation()}>
                <div className="modal-icon"><UsersRound size={22} /></div>
                <h2>Pessoas com acesso</h2>
                {dashboardAccess.length === 0 ? <p>Nenhum colaborador aceitou o convite ainda.</p> : (
                  <div className="notification-list">
                    {dashboardAccess.map((person) => (
                      <div className="collaborator-row" key={`${person.permission}-${person.user_id}`}>
                        <ProfileAvatar image={person.profile_image} name={person.name} />
                        <span><strong>@{person.username}</strong><small>{person.permission}</small></span>
                      </div>
                    ))}
                  </div>
                )}
                <button type="button" className="modal-confirm" onClick={() => setShowAccessModal(false)}>Fechar</button>
              </div>
            </div>
          )}
        </section>
      </main>
    </AppLayout>
  );
}
