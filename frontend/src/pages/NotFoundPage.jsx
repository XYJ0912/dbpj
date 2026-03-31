import { Link } from 'react-router-dom'
import { SectionHeader } from '../components/SectionHeader'

export function NotFoundPage() {
  return (
    <div className="page-stack page-stack--narrow">
      <SectionHeader
        eyebrow="404"
        title="This page does not exist in the current scaffold."
        subtitle="The router is in place, so you can keep extending the frontend from here."
        align="center"
      />
      <div className="screen-state">
        <Link className="accent-link" to="/">
          Return home
        </Link>
      </div>
    </div>
  )
}
