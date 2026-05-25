export function PublishReport({ report }) {
  if (!report) {
    return <div className="screen-state">Run a publish check to see the report.</div>
  }

  const items = report.items || [
    ...(report.warnings || []).map((item) => ({ ...item, severity: 'warning' })),
    ...(report.errors || []).map((item) => ({ ...item, severity: 'error' })),
  ]

  return (
    <div className="publish-report">
      <div className="metric-row">
        <span>Works: {report.summary?.works ?? 0}</span>
        <span>Assets: {report.summary?.assets ?? report.exported_assets_count ?? 0}</span>
        <span>Warnings: {report.summary?.warnings ?? 0}</span>
        <span>Errors: {report.summary?.errors ?? 0}</span>
      </div>
      <div className="report-list">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${item.check_type}-${index}`} className={`report-item report-item--${item.severity}`}>
              <strong>{item.check_type}</strong>
              <span>{item.message}</span>
            </div>
          ))
        ) : (
          <div className="report-item report-item--info">No blocking issues found.</div>
        )}
      </div>
    </div>
  )
}
