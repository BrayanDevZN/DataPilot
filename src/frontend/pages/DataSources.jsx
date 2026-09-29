import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  Database,
  FileSpreadsheet,
  Globe2,
  Plus,
  RefreshCcw,
  Server,
  Trash2,
  UploadCloud,
} from "lucide-react";

import AppLayout from "../components/AppLayout";
import Loading from "../components/Loading";
import { getToken } from "../utils/storage";

import {
  createDataSource,
  getDataSource,
  getDataSources,
  getLinkedDashboards,
  updateDataSource,
  deleteDataSource,
} from "../api/dataSourceApi";

import {
  refreshDashboards as refreshLinkedDashboards,
} from "../api/dashboardApi";

const ROWS_STEP = 25;
const SOURCE_TYPES = [
  { value: "file", label: "Arquivo", icon: FileSpreadsheet },
  { value: "web", label: "Web", icon: Globe2 },
  { value: "database", label: "Banco de dados", icon: Server },
];

const DEFAULT_DATABASE_CONNECTION = {
  dialect: "postgresql",
  host: "",
  port: "5432",
  database: "",
  username: "",
  password: "",
};

function createDefaultDatabaseConnection() {
  return { ...DEFAULT_DATABASE_CONNECTION };
}

function parseDatabaseUrl(databaseUrl = "") {
  if (!databaseUrl) return createDefaultDatabaseConnection();

  try {
    const parsedUrl = new URL(databaseUrl);
    const protocol = parsedUrl.protocol.replace(":", "") || "postgresql";

    return {
      dialect: protocol === "postgres" ? "postgresql" : protocol,
      host: parsedUrl.hostname || "",
      port: parsedUrl.port || (protocol.includes("postgres") ? "5432" : ""),
      database: decodeURIComponent(parsedUrl.pathname.replace(/^\//, "")),
      username: decodeURIComponent(parsedUrl.username || ""),
      password: decodeURIComponent(parsedUrl.password || ""),
    };
  } catch {
    return createDefaultDatabaseConnection();
  }
}

function buildDatabaseUrl(config) {
  const dialect = config.dialect || "postgresql";
  const auth =
    config.username || config.password
      ? `${encodeURIComponent(config.username)}:${encodeURIComponent(config.password)}@`
      : "";
  const port = config.port ? `:${config.port}` : "";
  const database = config.database
    ? `/${encodeURIComponent(config.database)}`
    : "";

  return `${dialect}://${auth}${config.host}${port}${database}`;
}

export default function DataSources() {
  const [dataSources, setDataSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showLinkedDashboardsModal, setShowLinkedDashboardsModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const [sourceName, setSourceName] = useState("");
  const [sourceType, setSourceType] = useState("file");
  const [sourceFile, setSourceFile] = useState(null);
  const [apiUrl, setApiUrl] = useState("");
  const [databaseConnection, setDatabaseConnection] = useState(
    createDefaultDatabaseConnection
  );
  const [databaseQuery, setDatabaseQuery] = useState("");
  const [refreshIntervalDays, setRefreshIntervalDays] = useState("");
  const [updateSourceType, setUpdateSourceType] = useState("file");
  const [updateFile, setUpdateFile] = useState(null);
  const [updateApiUrl, setUpdateApiUrl] = useState("");
  const [updateDatabaseConnection, setUpdateDatabaseConnection] = useState(
    createDefaultDatabaseConnection
  );
  const [updateDatabaseQuery, setUpdateDatabaseQuery] = useState("");
  const [updateRefreshIntervalDays, setUpdateRefreshIntervalDays] = useState("");
  const [pendingUpdateFile, setPendingUpdateFile] = useState(null);
  const [pendingUpdatePayload, setPendingUpdatePayload] = useState(null);
  const [linkedDashboards, setLinkedDashboards] = useState([]);

  const [visibleRows, setVisibleRows] = useState(ROWS_STEP);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [loadingUpdate, setLoadingUpdate] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);
  const [loadingLinkedDashboards, setLoadingLinkedDashboards] = useState(false);
  const [loadingRefreshDashboards, setLoadingRefreshDashboards] = useState(false);

  const [error, setError] = useState("");

  async function loadDataSources({ silentFetchFailure = false } = {}) {
    try {
      setLoadingList(true);
      setError("");

      const token = getToken();
      const response = await getDataSources(token);

      const sources = response?.data_sources || [];
      setDataSources(sources);
      refreshAutomaticallySyncedDashboards(response);

      if (!selectedSource && sources.length > 0) {
        await openDataSource(sources[0].id);
      }
    } catch (err) {
      const message = err.message || "Erro ao buscar fontes de dados.";

      if (silentFetchFailure || isLikelyFetchFailure(err)) {
        console.warn("Fontes indisponiveis no carregamento inicial:", err);
        return;
      }

      setError(message);
      toast.error(message);
    } finally {
      setLoadingList(false);
    }
  }

  async function openDataSource(dataSourceId) {
    try {
      setError("");
      setVisibleRows(ROWS_STEP);

      const token = getToken();
      const response = await getDataSource(token, dataSourceId);

      setSelectedSource(response?.data_source || null);
    } catch (err) {
      const message = err.message || "Erro ao abrir fonte de dados.";
      setError(message);
      toast.error(message);
    }
  }

  async function refreshDataSourcesAndFind(matchFn) {
    const token = getToken();
    const response = await getDataSources(token);
    const sources = response?.data_sources || [];

    setDataSources(sources);

    return sources.find(matchFn) || null;
  }

  function normalizeSourceLookup(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }

  function isSameCreatedSource(source, wantedName, wantedFile) {
    const sourceName = normalizeSourceLookup(source?.name);
    const sourceFileName = normalizeSourceLookup(source?.file_name);
    const nextName = normalizeSourceLookup(wantedName);
    const nextFileName = normalizeSourceLookup(wantedFile?.name);

    return (
      sourceName === nextName ||
      (nextFileName && sourceFileName === nextFileName)
    );
  }

  async function waitForDataSource(matchFn, attempts = 8) {
    let lastError = null;

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const source = await refreshDataSourcesAndFind(matchFn);

        if (source) {
          return source;
        }
      } catch (err) {
        lastError = err;
      }

      if (attempt < attempts - 1) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
      }
    }

    if (lastError) {
      throw lastError;
    }

    return null;
  }

  function addOrReplaceDataSource(source) {
    if (!source?.id) return;

    setDataSources((currentSources) => {
      const exists = currentSources.some(
        (currentSource) => Number(currentSource.id) === Number(source.id)
      );

      if (exists) {
        return currentSources.map((currentSource) =>
          Number(currentSource.id) === Number(source.id)
            ? { ...currentSource, ...source }
            : currentSource
        );
      }

      return [source, ...currentSources];
    });
  }

  async function reloadDataSourcesQuietly() {
    try {
      await loadDataSources({ silentFetchFailure: true });
    } catch (err) {
      console.warn("Nao foi possivel recarregar fontes em segundo plano:", err);
    }
  }

  function isLikelyFetchFailure(error) {
    const message = String(error?.message || "").toLowerCase();

    return (
      message.includes("failed to fetch") ||
      message.includes("requisição demorou") ||
      message.includes("conexão foi interrompida") ||
      message.includes("requisição demorou") ||
      message.includes("conexão foi interrompida") ||
      error instanceof TypeError
    );
  }

  function getSourceTypeLabel(value) {
    return SOURCE_TYPES.find((item) => item.value === value)?.label || "Arquivo";
  }

  function getSourceDescription(source) {
    const label = getSourceTypeLabel(source?.source_type);
    const config = source?.connection_config || {};

    if (source?.source_type === "web") {
      return `${label} - ${config.url || source.file_name || "API externa"}`;
    }

    if (source?.source_type === "database") {
      return `${label} - ${config.database_url ? "conexao configurada" : "Banco de dados"}`;
    }

    return `${label} - ${source?.file_name || "Arquivo"}`;
  }

  function getRefreshNotice(days) {
    if (!days) return "";

    return `A cada ${days} dia${Number(days) === 1 ? "" : "s"}, esta fonte sera consultada de novo. Quando isso acontecer, os dashboards ligados serao reconstruidos automaticamente com o prompt salvo.`;
  }

  function updateDatabaseConnectionField(field, value) {
    setDatabaseConnection((currentValue) => ({
      ...currentValue,
      [field]: value,
    }));
  }

  function updateUpdateDatabaseConnectionField(field, value) {
    setUpdateDatabaseConnection((currentValue) => ({
      ...currentValue,
      [field]: value,
    }));
  }

  function buildCreatePayload() {
    return {
      sourceType,
      file: sourceFile,
      apiUrl,
      databaseUrl: buildDatabaseUrl(databaseConnection),
      query: databaseQuery,
      refreshIntervalDays,
    };
  }

  function buildUpdatePayload() {
    return {
      sourceType: updateSourceType,
      file: updateFile,
      apiUrl: updateApiUrl,
      databaseUrl: buildDatabaseUrl(updateDatabaseConnection),
      query: updateDatabaseQuery,
      refreshIntervalDays: updateRefreshIntervalDays,
    };
  }

  function validateSourcePayload(payload, fileMessage, databaseConfig) {
    if (payload.sourceType === "file" && !payload.file) {
      toast.error(fileMessage);
      return false;
    }

    if (payload.sourceType === "web" && !payload.apiUrl.trim()) {
      toast.error("Digite a URL da API.");
      return false;
    }

    if (payload.sourceType === "database") {
      const config = databaseConfig || createDefaultDatabaseConnection();

      if (!config.host.trim()) {
        toast.error("Digite o host do banco.");
        return false;
      }

      if (!config.port.trim()) {
        toast.error("Digite a porta do banco.");
        return false;
      }

      if (!config.database.trim()) {
        toast.error("Digite o nome do banco.");
        return false;
      }

      if (!config.username.trim()) {
        toast.error("Digite o usuario do banco.");
        return false;
      }

      if (!payload.query.trim()) {
        toast.error("Digite a query SELECT.");
        return false;
      }
    }

    return true;
  }

  async function refreshAutomaticallySyncedDashboards(response) {
    const dashboards = response?.auto_refresh_dashboards || [];

    if (!dashboards.length) return;

    try {
      setLoadingRefreshDashboards(true);
      await refreshLinkedDashboards({
        token: getToken(),
        dashboards,
      });
      toast.success("Fontes agendadas e dashboards vinculados foram atualizados.");
    } catch (err) {
      toast.error(err.message || "Fontes agendadas foram atualizadas; revise dashboards pendentes.");
    } finally {
      setLoadingRefreshDashboards(false);
    }
  }

  function resetUpdateState() {
    setUpdateFile(null);
    setPendingUpdateFile(null);
    setPendingUpdatePayload(null);
    setLinkedDashboards([]);
    setShowUpdateModal(false);
    setShowLinkedDashboardsModal(false);
  }

  function closeCreateModal() {
    if (loadingCreate) return;

    setSourceName("");
    setSourceType("file");
    setSourceFile(null);
    setApiUrl("");
    setDatabaseConnection(createDefaultDatabaseConnection());
    setDatabaseQuery("");
    setRefreshIntervalDays("");
    setShowCreateModal(false);
  }

  function openUpdateModal() {
    if (!selectedSource) return;

    const config = selectedSource.connection_config || {};
    const nextType = selectedSource.source_type || "file";

    setUpdateSourceType(nextType);
    setUpdateFile(null);
    setUpdateApiUrl(config.url || "");
    setUpdateDatabaseConnection(parseDatabaseUrl(config.database_url || ""));
    setUpdateDatabaseQuery(config.query || "");
    setUpdateRefreshIntervalDays(selectedSource.refresh_interval_days || "");
    setShowUpdateModal(true);
  }

  function closeUpdateModal() {
    if (loadingUpdate || loadingLinkedDashboards || loadingRefreshDashboards) return;

    resetUpdateState();
  }

  async function handleCreateSource(event) {
    event.preventDefault();

    if (!sourceName.trim()) {
      toast.error("Digite o nome da fonte.");
      return;
    }

    const sourcePayload = buildCreatePayload();

    if (
      !validateSourcePayload(
        sourcePayload,
        "Selecione um arquivo.",
        databaseConnection
      )
    ) {
      return;
    }

    try {
      setLoadingCreate(true);
      setError("");

      const token = getToken();

      const response = await createDataSource({
        token,
        name: sourceName.trim(),
        ...sourcePayload,
      });

      const createdSource = response?.data_source;

      toast.success("Fonte de dados criada com sucesso.");

      if (createdSource) {
        addOrReplaceDataSource(createdSource);
        setSelectedSource(createdSource);
      }

      closeCreateModal();
      reloadDataSourcesQuietly();
    } catch (err) {
      try {
        const createdSource = await waitForDataSource(
          (source) =>
            isSameCreatedSource(source, sourceName, sourceFile)
        );

        if (createdSource) {
          toast.success("Fonte de dados criada com sucesso.");

          closeCreateModal();

          await openDataSource(createdSource.id);
          return;
        }
      } catch (refreshError) {
        console.error("Erro ao verificar se a fonte foi salva:", refreshError);
      }

      const message = isLikelyFetchFailure(err)
        ? "O arquivo foi enviado, mas o servidor ainda esta processando. Aguarde alguns segundos e atualize a lista."
        : err.message || "Erro ao criar fonte de dados.";

      if (isLikelyFetchFailure(err) && sourcePayload.sourceType === "file") {
        setError("");
        toast.info(message);
        reloadDataSourcesQuietly();
      } else {
        setError(message);
        toast.error(message);
      }
    } finally {
      setLoadingCreate(false);
    }
  }

  async function handleUpdateSource(event) {
    event.preventDefault();

    if (!selectedSource?.id) {
      toast.error("Selecione uma fonte primeiro.");
      return;
    }

    const updatePayload = buildUpdatePayload();

    if (
      !validateSourcePayload(
        updatePayload,
        "Selecione a nova planilha.",
        updateDatabaseConnection
      )
    ) {
      return;
    }

    try {
      setLoadingLinkedDashboards(true);
      setError("");

      const token = getToken();

      const response = await getLinkedDashboards(
        token,
        selectedSource.id
      );

      const dashboards = response?.dashboards || [];

      setPendingUpdateFile(updateFile);
      setPendingUpdatePayload(updatePayload);
      setLinkedDashboards(dashboards);

      if (dashboards.length > 0) {
        setShowUpdateModal(false);
        setShowLinkedDashboardsModal(true);
        return;
      }

      await executeUpdateSource({
        shouldRefreshDashboards: false,
        dashboardsToRefresh: [],
        payload: updatePayload,
      });
    } catch (err) {
      const message = err.message || "Erro ao verificar dashboards vinculados.";
      setError(message);
      toast.error(message);
    } finally {
      setLoadingLinkedDashboards(false);
    }
  }

  async function executeUpdateSource({
    shouldRefreshDashboards,
    dashboardsToRefresh,
    fileToUpload,
    payload,
  }) {
    if (!selectedSource?.id) {
      toast.error("Selecione uma fonte primeiro.");
      return;
    }

    const finalPayload = payload || {
      ...buildUpdatePayload(),
      file: fileToUpload,
    };

    if (
      !validateSourcePayload(
        finalPayload,
        "Selecione a nova planilha.",
        updateDatabaseConnection
      )
    ) {
      return;
    }

    try {
      setLoadingUpdate(true);
      setError("");

      const token = getToken();

      const response = await updateDataSource({
        token,
        data_source_id: selectedSource.id,
        ...finalPayload,
        refreshDashboards: shouldRefreshDashboards,
      });

      const updatedSource = response?.data_source;

      if (shouldRefreshDashboards && dashboardsToRefresh.length > 0) {
        setLoadingRefreshDashboards(true);

        await refreshLinkedDashboards({
          token,
          dashboards: dashboardsToRefresh,
        });

        toast.success("Fonte e dashboards vinculados atualizados com sucesso.");
      } else {
        toast.success("Fonte atualizada com sucesso.");
      }

      resetUpdateState();

      await loadDataSources();

      if (updatedSource?.id) {
        await openDataSource(updatedSource.id);
      }
    } catch (err) {
      try {
        const updatedSource = await refreshDataSourcesAndFind(
          (source) => Number(source.id) === Number(selectedSource.id)
        );

        if (updatedSource) {
          resetUpdateState();

          await openDataSource(updatedSource.id);

          toast.success(
            shouldRefreshDashboards
              ? "Fonte atualizada. Se algum dashboard ainda não mudou, atualize-o manualmente."
              : "Fonte atualizada com sucesso."
          );

          return;
        }
      } catch (refreshError) {
        console.error("Erro ao verificar se a fonte foi atualizada:", refreshError);
      }

      const message = isLikelyFetchFailure(err)
        ? "A fonte pode ter sido atualizada, mas a resposta demorou. Atualize a lista para conferir."
        : err.message || "Erro ao atualizar fonte.";

      setError(message);
      toast.error(message);
    } finally {
      setLoadingUpdate(false);
      setLoadingRefreshDashboards(false);
    }
  }

  async function handleUpdateOnlySource() {
    await executeUpdateSource({
      shouldRefreshDashboards: false,
      dashboardsToRefresh: [],
      fileToUpload: pendingUpdateFile,
      payload: pendingUpdatePayload,
    });
  }

  async function handleUpdateSourceAndDashboards() {
    await executeUpdateSource({
      shouldRefreshDashboards: true,
      dashboardsToRefresh: linkedDashboards,
      fileToUpload: pendingUpdateFile,
      payload: pendingUpdatePayload,
    });
  }

  async function confirmDeleteSource() {
    if (!selectedSource?.id) return;

    try {
      setLoadingDelete(true);
      setError("");

      const token = getToken();

      await deleteDataSource(token, selectedSource.id);

      toast.success("Fonte excluída com sucesso.");

      setSelectedSource(null);
      setVisibleRows(ROWS_STEP);
      setShowDeleteModal(false);

      await loadDataSources();
    } catch (err) {
      const message = err.message || "Erro ao excluir fonte.";
      setError(message);
      toast.error(message);
    } finally {
      setLoadingDelete(false);
    }
  }

  function handleShowMoreRows() {
    setVisibleRows((currentValue) => currentValue + ROWS_STEP);
  }

  useEffect(() => {
    loadDataSources();
  }, []);

  useEffect(() => {
    setVisibleRows(ROWS_STEP);
  }, [selectedSource?.id]);

  const allRows = Array.isArray(selectedSource?.file_data)
    ? selectedSource.file_data
    : [];

  const previewRows = allRows.slice(0, visibleRows);
  const hasMoreRows = previewRows.length < allRows.length;
  const previewColumns =
    previewRows.length > 0 ? Object.keys(previewRows[0]) : [];

  const isUpdatingSomething =
    loadingUpdate || loadingLinkedDashboards || loadingRefreshDashboards;

  function renderSourceTypeFields({
    currentSourceType,
    onSourceTypeChange,
    fileValue,
    onFileChange,
    apiUrlValue,
    onApiUrlChange,
    databaseConnectionValue,
    onDatabaseConnectionChange,
    databaseQueryValue,
    onDatabaseQueryChange,
    refreshIntervalValue,
    onRefreshIntervalChange,
    fileLabel,
  }) {
    const notice = getRefreshNotice(refreshIntervalValue);

    return (
      <>
        <label className="settings-label">
          Tipo de fonte
          <div className="source-type-grid">
            {SOURCE_TYPES.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  type="button"
                  key={item.value}
                  className={`source-type-button ${
                    currentSourceType === item.value ? "is-active" : ""
                  }`}
                  onClick={() => onSourceTypeChange(item.value)}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </label>

        {currentSourceType === "file" && (
          <label className="settings-label">
            {fileLabel}
            <label className="custom-file-upload">
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={(event) => onFileChange(event.target.files[0])}
              />
              <UploadCloud size={18} />
              <span>{fileValue ? fileValue.name : "Selecionar arquivo"}</span>
            </label>
          </label>
        )}

        {currentSourceType === "web" && (
          <>
            <label className="settings-label">
              URL da API
              <input
                value={apiUrlValue}
                onChange={(event) => onApiUrlChange(event.target.value)}
                placeholder="https://api.exemplo.com/dados"
              />
            </label>

            <label className="settings-label">
              Dias de atualizacao
              <input
                type="number"
                min="1"
                value={refreshIntervalValue}
                onChange={(event) => onRefreshIntervalChange(event.target.value)}
                placeholder="Ex: 7"
              />
            </label>
          </>
        )}

        {currentSourceType === "database" && (
          <>
            <label className="settings-label">
              Tipo do banco
              <select
                value={databaseConnectionValue.dialect}
                onChange={(event) =>
                  onDatabaseConnectionChange("dialect", event.target.value)
                }
              >
                <option value="postgresql">PostgreSQL</option>
              </select>
            </label>

            <div className="database-fields-grid">
              <label className="settings-label">
                Host
                <input
                  value={databaseConnectionValue.host}
                  onChange={(event) =>
                    onDatabaseConnectionChange("host", event.target.value)
                  }
                  placeholder="localhost ou db.exemplo.com"
                />
              </label>

              <label className="settings-label">
                Porta
                <input
                  type="number"
                  min="1"
                  value={databaseConnectionValue.port}
                  onChange={(event) =>
                    onDatabaseConnectionChange("port", event.target.value)
                  }
                  placeholder="5432"
                />
              </label>

              <label className="settings-label">
                Banco
                <input
                  value={databaseConnectionValue.database}
                  onChange={(event) =>
                    onDatabaseConnectionChange("database", event.target.value)
                  }
                  placeholder="postgres"
                />
              </label>

              <label className="settings-label">
                Usuario
                <input
                  value={databaseConnectionValue.username}
                  onChange={(event) =>
                    onDatabaseConnectionChange("username", event.target.value)
                  }
                  placeholder="postgres"
                />
              </label>
            </div>

            <label className="settings-label">
              Senha
              <input
                type="password"
                value={databaseConnectionValue.password}
                onChange={(event) =>
                  onDatabaseConnectionChange("password", event.target.value)
                }
                placeholder="Senha do banco"
              />
            </label>

            <label className="settings-label">
              Query SELECT
              <textarea
                value={databaseQueryValue}
                onChange={(event) => onDatabaseQueryChange(event.target.value)}
                placeholder="select * from public.vendas limit 5000"
              />
            </label>

            <label className="settings-label">
              Dias de atualizacao
              <input
                type="number"
                min="1"
                value={refreshIntervalValue}
                onChange={(event) => onRefreshIntervalChange(event.target.value)}
                placeholder="Ex: 7"
              />
            </label>
          </>
        )}

        {notice && <p className="source-refresh-notice">{notice}</p>}
      </>
    );
  }

  return (
    <AppLayout>
      <main className="data-sources-page">
        <section className="data-sources-header">
          <div>
            <span className="data-sources-eyebrow">
              <Database size={18} />
              Fontes de Dados
            </span>

            <h1>Gerencie suas fontes de dados</h1>

            <p>
              Adicione planilhas, atualize arquivos existentes e reutilize as
              mesmas fontes para criar vários dashboards.
            </p>
          </div>

          <div className="data-sources-actions">
            <button
              type="button"
              className="data-source-secondary-button"
              onClick={openUpdateModal}
              disabled={!selectedSource}
            >
              <RefreshCcw size={18} />
              Atualizar fonte
            </button>

            <button
              type="button"
              className="data-source-primary-button"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={18} />
              Adicionar fonte
            </button>
          </div>
        </section>

        {error && <p className="error-message">{error}</p>}

        <section className="data-sources-layout">
          <aside className="data-sources-panel">
            <div className="data-sources-panel-top">
              <h2>Suas fontes</h2>
              <span>{dataSources.length}</span>
            </div>

            <div className="data-sources-list">
              {loadingList ? (
                <Loading
                  compact
                  label="Carregando fontes"
                  description="Sincronizando seus arquivos."
                />
              ) : dataSources.length === 0 ? (
                <p className="data-source-empty">
                  Nenhuma fonte cadastrada ainda.
                </p>
              ) : (
                dataSources.map((source) => (
                  <button
                    key={source.id}
                    type="button"
                    className={`data-source-item ${
                      selectedSource?.id === source.id ? "is-active" : ""
                    }`}
                    onClick={() => openDataSource(source.id)}
                  >
                    <FileSpreadsheet size={18} />

                      <span>
                        <strong>{source.name}</strong>
                        <small>
                          {source.is_shared
                            ? `Compartilhada por @${source.creator_username}`
                            : getSourceDescription(source)}
                        </small>
                      </span>
                  </button>
                ))
              )}
            </div>
          </aside>

          <section className="data-source-content">
            {!selectedSource ? (
              <div className="data-source-empty-state">
                <Database size={46} />
                <h2>Selecione uma fonte</h2>
                <p>
                  Escolha uma fonte na lista ou adicione uma nova planilha para
                  começar.
                </p>
              </div>
            ) : (
              <>
                <div className="data-source-details-card">
                  <div>
                    <h2>{selectedSource.name}</h2>
                    <p>
                      {getSourceDescription(selectedSource)}
                    </p>
                  </div>

                  {!selectedSource.is_shared && (
                    <button
                      type="button"
                      className="data-source-danger-button"
                      onClick={() => setShowDeleteModal(true)}
                    >
                      <Trash2 size={18} />
                      Excluir
                    </button>
                  )}
                </div>

                <div className="data-source-stats">
                  <div>
                    <span>Linhas</span>
                    <strong>{selectedSource.row_count || 0}</strong>
                  </div>

                  <div>
                    <span>Colunas</span>
                    <strong>{selectedSource.column_count || 0}</strong>
                  </div>

                  <div>
                    <span>Arquivo</span>
                    <strong>{selectedSource.file_name || getSourceTypeLabel(selectedSource.source_type)}</strong>
                  </div>
                  <div>
                    <span>Atualizacao</span>
                    <strong>
                      {selectedSource.refresh_interval_days
                        ? `${selectedSource.refresh_interval_days} dia${Number(selectedSource.refresh_interval_days) === 1 ? "" : "s"}`
                        : "Manual"}
                    </strong>
                  </div>
                </div>

                <div className="data-source-preview-card">
                  <div className="data-source-preview-header">
                    <h3>Prévia dos dados</h3>
                    <span>
                      Mostrando {previewRows.length} de {allRows.length} linhas
                    </span>
                  </div>

                  {previewRows.length === 0 ? (
                    <p className="data-source-empty">
                      Nenhum dado disponível para visualização.
                    </p>
                  ) : (
                    <>
                      <div className="data-source-table-scroll">
                        <table className="data-source-table">
                          <thead>
                            <tr>
                              {previewColumns.map((column) => (
                                <th key={column}>{column}</th>
                              ))}
                            </tr>
                          </thead>

                          <tbody>
                            {previewRows.map((row, index) => (
                              <tr key={index}>
                                {previewColumns.map((column) => (
                                  <td key={column}>
                                    {row[column] === null ||
                                    row[column] === undefined
                                      ? "-"
                                      : String(row[column])}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {hasMoreRows && (
                        <div className="data-source-load-more">
                          <button
                            type="button"
                            onClick={handleShowMoreRows}
                          >
                            Ver mais
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </>
            )}
          </section>
        </section>

        {showCreateModal && (
          <div className="modal-overlay">
            <form
              className="modal-card modal-card-wide"
              onSubmit={handleCreateSource}
            >
              <div className="modal-icon">
                <UploadCloud size={22} />
              </div>

              <h2>Adicionar fonte</h2>
              <p>Escolha um nome e conecte arquivo, API externa ou banco.</p>

              <label className="settings-label">
                Nome da fonte
                <input
                  value={sourceName}
                  onChange={(event) => setSourceName(event.target.value)}
                  placeholder="Ex: Marketing 2026"
                  autoFocus
                />
              </label>

              {renderSourceTypeFields({
                currentSourceType: sourceType,
                onSourceTypeChange: setSourceType,
                fileValue: sourceFile,
                onFileChange: setSourceFile,
                apiUrlValue: apiUrl,
                onApiUrlChange: setApiUrl,
                databaseConnectionValue: databaseConnection,
                onDatabaseConnectionChange: updateDatabaseConnectionField,
                databaseQueryValue: databaseQuery,
                onDatabaseQueryChange: setDatabaseQuery,
                refreshIntervalValue: refreshIntervalDays,
                onRefreshIntervalChange: setRefreshIntervalDays,
                fileLabel: "Arquivo",
              })}

              <div className="modal-actions">
                <button
                  type="button"
                  className="modal-cancel"
                  onClick={closeCreateModal}
                  disabled={loadingCreate}
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  className="modal-confirm"
                  disabled={loadingCreate}
                >
                  {loadingCreate ? "Salvando..." : "Salvar fonte"}
                </button>
              </div>
            </form>
          </div>
        )}

        {showUpdateModal && (
          <div className="modal-overlay">
            <form
              className="modal-card modal-card-wide"
              onSubmit={handleUpdateSource}
            >
              <div className="modal-icon">
                <RefreshCcw size={22} />
              </div>

              <h2>Atualizar fonte</h2>

              <p>
                Altere os dados de conexao para substituir os dados de{" "}
                <strong>{selectedSource?.name}</strong>.
              </p>

              {renderSourceTypeFields({
                currentSourceType: updateSourceType,
                onSourceTypeChange: setUpdateSourceType,
                fileValue: updateFile,
                onFileChange: setUpdateFile,
                apiUrlValue: updateApiUrl,
                onApiUrlChange: setUpdateApiUrl,
                databaseConnectionValue: updateDatabaseConnection,
                onDatabaseConnectionChange: updateUpdateDatabaseConnectionField,
                databaseQueryValue: updateDatabaseQuery,
                onDatabaseQueryChange: setUpdateDatabaseQuery,
                refreshIntervalValue: updateRefreshIntervalDays,
                onRefreshIntervalChange: setUpdateRefreshIntervalDays,
                fileLabel: "Nova planilha",
              })}

              <div className="modal-actions">
                <button
                  type="button"
                  className="modal-cancel"
                  onClick={closeUpdateModal}
                  disabled={isUpdatingSomething}
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  className="modal-confirm"
                  disabled={isUpdatingSomething}
                >
                  {loadingLinkedDashboards
                    ? "Verificando dashboards..."
                    : loadingUpdate
                      ? "Atualizando..."
                      : "Continuar"}
                </button>
              </div>
            </form>
          </div>
        )}

        {showLinkedDashboardsModal && (
          <div className="modal-overlay">
            <div className="modal-card modal-card-wide">
              <div className="modal-icon">
                <RefreshCcw size={22} />
              </div>

              <h2>Atualizar dashboards vinculados?</h2>

              <p>
                Essa fonte está ligada a{" "}
                <strong>{linkedDashboards.length}</strong>{" "}
                dashboard{linkedDashboards.length === 1 ? "" : "s"}.
                Ao atualizar todos, as análises serão refeitas usando o mesmo
                prompt de cada dashboard.
              </p>

              <div className="linked-dashboard-list">
                {linkedDashboards.map((dashboard) => (
                  <div
                    key={dashboard.id}
                    className="linked-dashboard-item"
                  >
                    <strong>{dashboard.title}</strong>
                    <small>{dashboard.prompt}</small>
                  </div>
                ))}
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="modal-cancel"
                  onClick={handleUpdateOnlySource}
                  disabled={isUpdatingSomething}
                >
                  Atualizar só a fonte
                </button>

                <button
                  type="button"
                  className="modal-confirm"
                  onClick={handleUpdateSourceAndDashboards}
                  disabled={isUpdatingSomething}
                >
                  {loadingRefreshDashboards
                    ? "Atualizando dashboards..."
                    : loadingUpdate
                      ? "Atualizando fonte..."
                      : "Atualizar tudo"}
                </button>
              </div>

              <button
                type="button"
                className="modal-link-button"
                onClick={closeUpdateModal}
                disabled={isUpdatingSomething}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {showDeleteModal && (
          <div className="modal-overlay">
            <div className="modal-card">
              <div className="modal-icon modal-icon-danger">
                <Trash2 size={22} />
              </div>

              <h2>Excluir fonte</h2>

              <p>
                Tem certeza que deseja excluir{" "}
                <strong>{selectedSource?.name}</strong>?
              </p>

              <div className="modal-actions">
                <button
                  type="button"
                  className="modal-cancel"
                  onClick={() => setShowDeleteModal(false)}
                  disabled={loadingDelete}
                >
                  Cancelar
                </button>

                <button
                  type="button"
                  className="delete-confirm-button"
                  onClick={confirmDeleteSource}
                  disabled={loadingDelete}
                >
                  {loadingDelete ? "Excluindo..." : "Excluir"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </AppLayout>
  );
}
