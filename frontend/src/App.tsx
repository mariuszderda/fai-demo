import { Route, Routes } from "react-router-dom";

import AppShell from "@/components/layout/AppShell";
import DashboardPage from "@/pages/DashboardPage";
import DesignProbePage from "@/pages/_DesignProbe";
import IncidentDetailPage from "@/pages/IncidentDetailPage";
import IncidentsListPage from "@/pages/IncidentsListPage";
import MitreMatrixPage from "@/pages/MitreMatrixPage";
import SettingsPage from "@/pages/SettingsPage";

export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="incidents" element={<IncidentsListPage />} />
        <Route path="incidents/:id" element={<IncidentDetailPage />} />
        <Route path="mitre" element={<MitreMatrixPage />} />
        <Route path="settings" element={<SettingsPage />} />
        {import.meta.env.DEV ? <Route path="_probe" element={<DesignProbePage />} /> : null}
      </Route>
    </Routes>
  );
}

