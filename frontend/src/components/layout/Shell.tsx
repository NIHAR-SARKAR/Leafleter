import {
  Bell,
  Calendar,
  FileText,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Search,
  Settings,
  Shield,
  Target,
  Users
} from "lucide-react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import logo from '@/assets/images/leafleter-logo.png';
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Topics", href: "/topics", icon: MessageSquare },
  { name: "Providers", href: "/providers", icon: Shield },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Schedules", href: "/schedules", icon: Calendar },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "Competitors", href: "/competitors", icon: Target },
  { name: "Search", href: "/search", icon: Search },
  { name: "Team", href: "/users", icon: Users },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Shell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen overflow-hidden">
        <aside className="hidden w-64 flex-col border-r bg-card md:flex">
          <div className="flex h-16 items-center border-b px-6">
            <img src={logo} alt="Logo" className="mr-2 h-8 w-8" />
            <span className="text-lg font-bold">Leafleter</span>
          </div>
          <nav className="flex-1 space-y-1 p-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  <Icon className="mr-3 h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <div className="mb-2 text-sm font-medium">
              {user?.full_name || user?.email}
            </div>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </aside>
        <main className="flex flex-1 flex-col overflow-hidden">
          <header className="flex h-16 items-center justify-between border-b bg-card px-6">
            <h1 className="text-xl font-semibold"></h1>
            <div className="text-sm text-muted-foreground">
              {user?.role?.name}
            </div>
          </header>
          <div className="flex-1 overflow-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
