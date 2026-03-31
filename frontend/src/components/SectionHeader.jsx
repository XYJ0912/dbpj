export function SectionHeader({ eyebrow, title, subtitle, align = 'left' }) {
  return (
    <header className={`section-header section-header--${align}`}>
      {eyebrow ? <p className="section-header__eyebrow">{eyebrow}</p> : null}
      <h1 className="section-header__title">{title}</h1>
      {subtitle ? <p className="section-header__subtitle">{subtitle}</p> : null}
    </header>
  )
}
