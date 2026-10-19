import {
  BarChart3,
  Database,
  History,
  LayoutDashboard,
  Lightbulb,
  Settings,
  Sparkles,
  Table2,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  description: string;
  /** false = the page is an honest "coming soon" placeholder. */
  available: boolean;
}

export const navItems: NavItem[] = [
  { label: "Overview", path: "/", icon: LayoutDashboard, description: "Workspace status at a glance.", available: true },
  { label: "Database Connections", path: "/connections", icon: Database, description: "Connect and manage your PostgreSQL databases.", available: true },
  { label: "Schema Explorer", path: "/schema", icon: Table2, description: "Browse tables, columns and relationships.", available: true },
  { label: "AI Query Workspace", path: "/workspace", icon: Sparkles, description: "Ask questions about your data in plain English.", available: false },
  { label: "Query History", path: "/history", icon: History, description: "Review past questions, SQL and results.", available: false },
  { label: "Visualizations", path: "/visualizations", icon: BarChart3, description: "Turn query results into interactive charts.", available: false },
  { label: "Data Insights", path: "/insights", icon: Lightbulb, description: "Evidence-based findings computed from your results.", available: false },
  { label: "Settings", path: "/settings", icon: Settings, description: "Profile and appearance.", available: true },
];