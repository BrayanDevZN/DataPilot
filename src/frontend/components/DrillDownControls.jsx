import { ChevronLeft, Home } from "lucide-react";

export default function DrillDownControls({
  hierarchy,
  path,
  onBack,
  onReset,
  canGoBack,
}) {
  if (!Array.isArray(hierarchy) || hierarchy.length < 2) {
    return null;
  }

  const currentLevel = hierarchy[Math.min(path.length, hierarchy.length - 1)];

  return (
    <div className="drilldown-controls">
      <button
        type="button"
        className="drilldown-back-button"
        onClick={onBack}
        disabled={!canGoBack}
        title="Voltar um nivel"
      >
        <ChevronLeft size={16} />
        <span>Voltar</span>
      </button>

      <div className="drilldown-breadcrumb" aria-label="Caminho do drill-down">
        <button type="button" onClick={onReset} disabled={!canGoBack}>
          <Home size={14} />
          <span>{hierarchy[0]?.label || hierarchy[0]?.column}</span>
        </button>

        {path.map((entry, index) => (
          <span className="drilldown-crumb" key={`${entry.column}-${entry.value}-${index}`}>
            <span>/</span>
            <button type="button" onClick={() => onReset(index + 1)}>
              {entry.value}
            </button>
          </span>
        ))}

        <span className="drilldown-current">
          <span>/</span>
          <strong>{currentLevel?.label || currentLevel?.column}</strong>
        </span>
      </div>
    </div>
  );
}
