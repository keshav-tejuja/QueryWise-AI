import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { navItems } from "@/config/navigation";
import { ProtectedRoute, PublicOnlyRoute } from "@/features/auth/routes";
import { ComingSoonPage } from "@/pages/ComingSoonPage";
import { ConnectionsPage } from "@/pages/ConnectionsPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { OverviewPage } from "@/pages/OverviewPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { SchemaExplorerPage } from "@/pages/SchemaExplorerPage";
import { SettingsPage } from "@/pages/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          {/* Every signed-in page must be a child of AppShell to get the sidebar and header. */}
          <Route element={<AppShell />}>
            <Route index element={<OverviewPage />} />
            <Route path="connections" element={<ConnectionsPage />} />
            <Route path="schema" element={<SchemaExplorerPage />} />
            <Route path="settings" element={<SettingsPage />} />
            {navItems
              .filter((item) => !item.available)
              .map((item) => (
                <Route key={item.path} path={item.path.slice(1)} element={<ComingSoonPage item={item} />} />
              ))}
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}