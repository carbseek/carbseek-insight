import { ENTITIES } from '../entities.js';
import EntityPage from './EntityPage.jsx';

// GET /api/reports now returns the full list, so reports use the generic
// list + create/edit/delete page like every other entity.
export default function ReportsPage() {
  return <EntityPage config={ENTITIES.reports} />;
}
