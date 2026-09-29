export default function Loading({
  label = "Carregando...",
  description = "",
  compact = false,
  overlay = false,
}) {
  return (
    <div
      className={`dp-loading ${compact ? "dp-loading-compact" : ""} ${
        overlay ? "dp-loading-overlay" : ""
      }`}
      role="status"
      aria-live="polite"
    >
      <span className="dp-loading-orbit" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>

      <span className="dp-loading-copy">
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
    </div>
  );
}
