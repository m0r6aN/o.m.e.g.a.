"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  BarChart3,
  Bot,
  Settings,
  Wrench,
  Home,
  GitBranch,
  Terminal,
  HelpCircle,
  Activity,
  FileText,
  User,
  Moon,
  Sun,
  LucideIcon
} from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";

interface SidebarItem {
  name: string;
  href: string;
  icon: LucideIcon;
  isExternal?: boolean;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
}

const mainNavItems: SidebarItem[] = [
  { name: "Home", href: "/", icon: Home },
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
];

const managementItems: SidebarItem[] = [
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Tools", href: "/tools", icon: Wrench },
  { name: "Workflows", href: "/workflows", icon: GitBranch },
];

const systemItems: SidebarItem[] = [
  { name: "Console", href: "/console", icon: Terminal },
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Documentation", href: "https://github.com/yourusername/omega-framework", icon: FileText, isExternal: true },
  { name: "Help", href: "/help", icon: HelpCircle },
];

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();
  const { setTheme, theme } = useTheme();
  
  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };
  
  const sections: SidebarSection[] = [
    { title: "Navigation", items: mainNavItems },
    { title: "Management", items: managementItems },
    { title: "System", items: systemItems },
  ];

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <div className={cn("pb-12 w-64 bg-background border-r flex flex-col h-screen", className)}>
      <div className="space-y-4 py-4 flex flex-col h-full">
        <div className="px-3 py-2 flex items-center mb-6">
          <div className="text-2xl font-bold text-center w-full bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            O.M.E.G.A
          </div>
        </div>
        
        <div className="flex-1 overflow-auto px-3 space-y-6">
          {sections.map((section) => (
            <div key={section.title} className="space-y-2">
              <h2 className="mb-2 px-4 text-xs font-semibold tracking-tight text-muted-foreground">
                {section.title}
              </h2>
              <div className="space-y-1">
                {section.items.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    target={item.isExternal ? "_blank" : undefined}
                    rel={item.isExternal ? "noopener noreferrer" : undefined}
                  >
                    <div
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                        isActive(item.href)
                          ? "bg-accent text-accent-foreground"
                          : "hover:bg-muted text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.name}</span>
                      {item.isExternal && (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="12"
                          height="12"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="ml-auto"
                        >
                          <path d="M7 7h10v10" />
                          <path d="M7 17L17 7" />
                        </svg>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="px-3 mt-auto pt-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-muted-foreground">System Online</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="h-8 w-8"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
          <div className="mt-4 flex items-center justify-center">
            <span className="text-xs text-muted-foreground">v0.1.0-alpha</span>
          </div>
        </div>
      </div>
    </div>
  );
}