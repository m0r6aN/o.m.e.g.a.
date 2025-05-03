"use client";

import React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BellIcon, SearchIcon, UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import toast, { Toaster } from 'react-hot-toast';
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Input } from "@/components/ui/input";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  
  // Get the current page title based on the pathname
  const getPageTitle = () => {
    const path = pathname.split("/").filter(Boolean);
    if (path.length === 1 && path[0] === "dashboard") {
      return "Dashboard";
    }
    
    // For nested routes, show the last segment of the path, capitalized
    if (path.length > 1) {
      const lastSegment = path[path.length - 1];
      if (lastSegment.match(/^\[.*\]$/)) {
        // Handle dynamic routes by showing the parent path capitalized
        const parentSegment = path[path.length - 2];
        return parentSegment.charAt(0).toUpperCase() + parentSegment.slice(1);
      }
      return lastSegment.charAt(0).toUpperCase() + lastSegment.slice(1);
    }
    
    return "Dashboard";
  };
  
  const pageTitle = getPageTitle();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar className="h-screen" />
      
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top navigation bar */}
        <header className="border-b bg-card px-6 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold">{pageTitle}</h1>
            
            <div className="flex items-center space-x-4">
              {/* Search bar */}
              <div className="relative w-64">
                <SearchIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search..."
                  className="pl-8"
                />
              </div>
              
              {/* Notification button */}
              <Button variant="ghost" size="icon" className="relative">
                <BellIcon className="h-5 w-5" />
                <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
                  3
                </span>
              </Button>
              
              {/* Theme toggle */}
              <ThemeToggle />
              
              {/* User profile */}
              <Button variant="ghost" size="icon">
                <UserIcon className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </header>
        
        {/* Main content area */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}