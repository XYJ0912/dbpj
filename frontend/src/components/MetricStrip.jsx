export function MetricStrip({ metrics }) {
  return (
    <div className="metric-strip">
      {metrics.map((metric) => (
        <div key={metric.label} className="metric-strip__item">
          <span className="metric-strip__value">{metric.value ?? 0}</span>
          <span className="metric-strip__label">{metric.label}</span>
        </div>
      ))}
    </div>
  )
}
