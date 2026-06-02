import { createBrowserRouter, Navigate } from "react-router-dom";
import App from "../App";
import Dashboard from "../pages/Dashboard";
import History from "../pages/History";
import LineageReview from "../pages/LineageReview";
import MetadataPanorama from "../pages/MetadataPanorama";
import MetadataQuality from "../pages/MetadataQuality";
import ProcedureLineage from "../pages/ProcedureLineage";
import SqlAnalyze from "../pages/SqlAnalyze";
import SqlRiskCheck from "../pages/SqlRiskCheck";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <Dashboard /> },
      { path: "metadata", element: <MetadataPanorama /> },
      { path: "metadata-quality", element: <MetadataQuality /> },
      { path: "procedure-lineage", element: <ProcedureLineage /> },
      { path: "lineage-review", element: <LineageReview /> },
      { path: "sql-analyze", element: <SqlAnalyze /> },
      { path: "sql-risk-check", element: <SqlRiskCheck /> },
      { path: "history", element: <History /> }
    ]
  }
]);
