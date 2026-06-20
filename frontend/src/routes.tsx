import { createBrowserRouter, Navigate } from "react-router-dom";

import { Shell } from "@/components/layout/Shell";
import { ActionsView } from "@/intelligence/pages/ActionsView";
import { BriefingView } from "@/intelligence/pages/BriefingView";
import { EntityDetail } from "@/intelligence/pages/EntityDetail";
import { TodayView } from "@/intelligence/pages/TodayView";
import { AlertRules } from "@/pages/AlertRules";
import { AskComrade } from "@/pages/AskComrade";
import { Competitors } from "@/pages/Competitors";
import { Dashboard } from "@/pages/Dashboard";
import { Facts } from "@/pages/Facts";
import { Integrations } from "@/pages/Integrations";
import { Login } from "@/pages/Login";
import { Newsfeed } from "@/pages/Newsfeed";
import { Newsletters } from "@/pages/Newsletters";
import { Providers } from "@/pages/Providers";
import { Register } from "@/pages/Register";
import { Reports } from "@/pages/Reports";
import { Schedules } from "@/pages/Schedules";
import { Search } from "@/pages/Search";
import { Settings } from "@/pages/Settings";
import { TopicDetail } from "@/pages/TopicDetail";
import { Topics } from "@/pages/Topics";
import { Users } from "@/pages/Users";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/register",
    element: <Register />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <Shell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: "topics", element: <Topics /> },
      { path: "topics/:id", element: <TopicDetail /> },
      { path: "providers", element: <Providers /> },
      { path: "reports", element: <Reports /> },
      { path: "schedules", element: <Schedules /> },
      { path: "alerts", element: <AlertRules /> },
      { path: "competitors", element: <Competitors /> },
      { path: "search", element: <Search /> },
      { path: "users", element: <Users /> },
      { path: "intelligence", element: <TodayView /> },
      { path: "newsfeed", element: <Newsfeed /> },
      { path: "facts", element: <Facts /> },
      { path: "ask", element: <AskComrade /> },
      { path: "integrations", element: <Integrations /> },
      { path: "newsletters", element: <Newsletters /> },
      { path: "intelligence/actions", element: <ActionsView /> },
      { path: "intelligence/entity/:entityType/:entityId", element: <EntityDetail /> },
      { path: "intelligence/brief/:briefType", element: <BriefingView /> },
      { path: "settings", element: <Settings /> },
    ],
  },
]);
