import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ProjectProvider } from "./shared/context/ProjectContext";
import Layout from "./shared/components/Layout";
import DataModelPage from "./modules/data-model/DataModelPage";
import LiquidPage from "./modules/liquid-generator/LiquidPage";
import MigrationPage from "./modules/migration/MigrationPage";
import ExplorerPage from "./pages/ExplorerPage";
import HistoryPage from "./pages/HistoryPage";
import SettingsPage from "./pages/SettingsPage";
import ProjectPage from "./pages/ProjectPage";

export default function App() {
  return (
    <BrowserRouter>
      <ProjectProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/data-model" replace />} />
            <Route path="/data-model" element={<DataModelPage />} />
            <Route path="/data-model/explorer" element={<DataModelPage />} />
            <Route path="/liquid" element={<LiquidPage />} />
            <Route path="/migration" element={<MigrationPage />} />
            <Route path="/explorer" element={<ExplorerPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/projects" element={<ProjectPage />} />
            <Route path="/projects/:id" element={<ProjectPage />} />
            <Route path="*" element={<Navigate to="/data-model" replace />} />
          </Route>
        </Routes>
      </ProjectProvider>
    </BrowserRouter>
  );
}
