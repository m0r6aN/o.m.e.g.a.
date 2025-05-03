# =========================================================
# OMEGA UI - Project Setup Script
# =========================================================
# This script creates the directory structure and initial files
# for the OMEGA UI Next.js application
# =========================================================

$ErrorActionPreference = "Stop"

# ANSI color codes for styling
$ESC = [char]27
$Green = "$ESC[32m"
$Cyan = "$ESC[36m"
$Yellow = "$ESC[33m"
$Red = "$ESC[31m"
$Bold = "$ESC[1m"
$Reset = "$ESC[0m"

# Banner function
function Show-Banner {
    Write-Host ""
    Write-Host "$Bold$Cyan   ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗ $Reset"
    Write-Host "$Bold$Cyan  ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗$Reset"
    Write-Host "$Bold$Cyan  ██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║$Reset"
    Write-Host "$Bold$Cyan  ██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║$Reset"
    Write-Host "$Bold$Cyan  ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║$Reset"
    Write-Host "$Bold$Cyan   ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝$Reset"
    Write-Host "$Yellow                                                $Reset"
    Write-Host "$Yellow  Orchestrated Multi-Expert Gen Agents UI Setup $Reset"
    Write-Host "$Yellow                                                $Reset"
    Write-Host ""
}

function Log-Step {
    param (
        [string]$message
    )
    Write-Host "$Bold$Green[OMEGA]$Reset $message"
}

function Log-Success {
    param (
        [string]$message
    )
    Write-Host "$Green✓ $message$Reset"
}

function Log-Warning {
    param (
        [string]$message
    )
    Write-Host "$Yellow⚠ $message$Reset"
}

function Log-Error {
    param (
        [string]$message
    )
    Write-Host "$Red✗ $message$Reset"
}

function Create-Directory {
    param (
        [string]$path
    )
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Log-Success "Created directory: $path"
    }
    else {
        Log-Warning "Directory already exists: $path"
    }
}

function Create-File {
    param (
        [string]$path,
        [string]$content = ""
    )
    
    if (-not (Test-Path $path)) {
        New-Item -ItemType File -Path $path -Force | Out-Null
        if ($content -ne "") {
            Set-Content -Path $path -Value $content
        }
        Log-Success "Created file: $path"
    }
    else {
        Log-Warning "File already exists: $path"
    }
}

# Main execution
Show-Banner
$rootDir = Read-Host "Enter the path where you want to create the OMEGA UI project (default: ./omega-ui)"
if ([string]::IsNullOrWhiteSpace($rootDir)) {
    $rootDir = "./omega-ui"
}

Log-Step "Creating project directory at $rootDir"
Create-Directory $rootDir

# Create base structure
Log-Step "Creating base directory structure..."
$directories = @(
    "$rootDir/public",
    "$rootDir/public/icons",
    "$rootDir/public/images",
    "$rootDir/src",
    "$rootDir/src/app",
    "$rootDir/src/app/api",
    "$rootDir/src/app/dashboard",
    "$rootDir/src/app/agents",
    "$rootDir/src/app/agents/[id]",
    "$rootDir/src/app/agents/create",
    "$rootDir/src/app/tools",
    "$rootDir/src/app/tools/[id]",
    "$rootDir/src/app/tools/create",
    "$rootDir/src/app/workflows",
    "$rootDir/src/app/workflows/[id]",
    "$rootDir/src/app/workflows/create",
    "$rootDir/src/app/settings",
    "$rootDir/src/app/settings/profile",
    "$rootDir/src/app/settings/appearance",
    "$rootDir/src/app/login",
    "$rootDir/src/app/register",
    "$rootDir/src/components",
    "$rootDir/src/components/ui",
    "$rootDir/src/components/layout",
    "$rootDir/src/components/agents",
    "$rootDir/src/components/tools",
    "$rootDir/src/components/workflows",
    "$rootDir/src/components/dashboard",
    "$rootDir/src/components/visualizations",
    "$rootDir/src/hooks",
    "$rootDir/src/lib",
    "$rootDir/src/lib/mcp",
    "$rootDir/src/lib/api",
    "$rootDir/src/types",
    "$rootDir/src/providers",
    "$rootDir/scripts"
)

foreach ($dir in $directories) {
    Create-Directory $dir
}

# Create package.json
Log-Step "Creating package.json..."
$packageJsonPath = Join-Path -Path $rootDir -ChildPath "package.json"
$packageJsonContent = @'
{
  "name": "omega-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write ."
  },
  "dependencies": {
    "@hookform/resolvers": "^3.3.4",
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "@tanstack/react-query": "^5.20.2",
    "@tanstack/react-query-devtools": "^5.20.2",
    "axios": "^1.6.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "d3": "^7.8.5",
    "lodash": "^4.17.21",
    "lucide-react": "^0.263.1",
    "next": "^14.1.0",
    "next-themes": "^0.2.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.50.1",
    "recharts": "^2.12.0",
    "tailwind-merge": "^2.2.1",
    "tailwindcss-animate": "^1.0.7",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/d3": "^7.4.3",
    "@types/lodash": "^4.14.202",
    "@types/node": "^20.11.16",
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.21.0",
    "@typescript-eslint/parser": "^6.21.0",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.1.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-react": "^7.33.2",
    "husky": "^8.0.3",
    "lint-staged": "^15.2.0",
    "postcss": "^8.4.35",
    "prettier": "^3.2.5",
    "prettier-plugin-tailwindcss": "^0.5.11",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3"
  }
}
'@
Create-File -path $packageJsonPath -content $packageJsonContent

# Create basic configuration files
Log-Step "Creating configuration files..."
Create-File -path "$rootDir/.env" -content "NEXT_PUBLIC_API_URL=http://localhost:8080"

$gitignoreContent = @'
# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
'@
Create-File -path "$rootDir/.gitignore" -content $gitignoreContent

$nextConfigContent = @'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
};

module.exports = nextConfig;
'@
Create-File -path "$rootDir/next.config.js" -content $nextConfigContent

$tsconfigContent = @'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
'@
Create-File -path "$rootDir/tsconfig.json" -content $tsconfigContent

# Create tailwind config
Log-Step "Creating Tailwind CSS configuration..."
$tailwindConfigContent = @'
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom OMEGA theme colors
        omega: {
          primary: {
            DEFAULT: "#1E40AF", // Deep blue
            light: "#3B82F6",   // Lighter blue
            dark: "#1E3A8A",    // Darker blue
          },
          secondary: {
            DEFAULT: "#7C3AED", // Purple
            light: "#A78BFA",   // Lighter purple
            dark: "#5B21B6",    // Darker purple
          },
          accent: {
            DEFAULT: "#10B981", // Green
            light: "#34D399",   // Lighter green
            dark: "#059669",    // Darker green
          },
          error: "#EF4444",     // Red
          warning: "#F59E0B",   // Amber
          info: "#3B82F6",      // Blue
          success: "#10B981",   // Green
        },
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
'@
Create-File -path "$rootDir/tailwind.config.js" -content $tailwindConfigContent

$postcssConfigContent = @'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'@
Create-File -path "$rootDir/postcss.config.js" -content $postcssConfigContent

# Create global CSS
Log-Step "Creating global CSS..."
$globalCssContent = @'
@tailwind base;
@tailwind components;
@tailwind utilities;
 
@layer base {
  :root {
    --background: 210 40% 98%;
    --foreground: 222.2 84% 4.9%;

    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
 
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
 
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
 
    --secondary: 250 95% 58%;
    --secondary-foreground: 210 40% 98%;
 
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
 
    --accent: 161.4 93.5% 30.4%;
    --accent-foreground: 210 40% 98%;
 
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
 
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
 
    --radius: 0.5rem;
  }
 
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
 
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
 
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
 
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
 
    --secondary: 250 95% 58%;
    --secondary-foreground: 210 40% 98%;
 
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
 
    --accent: 161.4 93.5% 30.4%;
    --accent-foreground: 210 40% 98%;
 
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
 
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}
 
@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
'@
Create-File -path "$rootDir/src/app/globals.css" -content $globalCssContent

# Create providers
Log-Step "Creating providers..."
$themeProviderContent = @'
"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes/dist/types";

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
'@
Create-File -path "$rootDir/src/providers/theme-provider.tsx" -content $themeProviderContent

# Create utility files
Log-Step "Creating utility files..."
$utilsContent = @'
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
'@
Create-File -path "$rootDir/src/lib/utils.ts" -content $utilsContent

# Create main app files
Log-Step "Creating basic app files..."
$layoutContent = @'
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/providers/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OMEGA Framework",
  description: "Orchestrated Multi-Expert Gen Agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
'@
Create-File -path "$rootDir/src/app/layout.tsx" -content $layoutContent

$pageContent = @'
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          O.M.E.G.A Framework
        </h1>
        <p className="text-xl mb-10">
          Orchestrated Multi-Expert Gen Agents
        </p>
        <Link 
          href="/dashboard" 
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
        >
          Enter Dashboard
        </Link>
      </div>
    </main>
  );
}
'@
Create-File -path "$rootDir/src/app/page.tsx" -content $pageContent

$dashboardPageContent = @'
export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <p>Welcome to the OMEGA Framework Dashboard!</p>
    </div>
  );
}
'@
Create-File -path "$rootDir/src/app/dashboard/page.tsx" -content $dashboardPageContent

# Create README
Log-Step "Creating README..."
$readmeContent = @'
# OMEGA UI

A modern UI for the Orchestrated Multi-Expert Gen Agents (OMEGA) Framework.

## Getting Started

First, install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

- Built with Next.js 14 and App Router
- Styling with Tailwind CSS
- UI components from Shadcn UI
- Dark mode support
- MCP (Model Context Protocol) integration
- Agent & Tool Management
- Workflow Builder and Visualization
- Real-time monitoring and metrics

## Learn More

- [OMEGA Framework Documentation](https://github.com/yourusername/omega-framework)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/)
- [Shadcn UI](https://ui.shadcn.com/)
'@
Create-File -path "$rootDir/README.md" -content $readmeContent

# Create installation script
Log-Step "Creating setup script..."
$setupEnvContent = @'
// Setup environment variables
const fs = require("fs");
const path = require("path");

// Define environment variables
const envContent = `NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_MCP_REGISTRY_URL=http://localhost:8080/registry
`;

// Write to .env.local file
fs.writeFileSync(path.join(__dirname, "..", ".env.local"), envContent);

console.log("✅ Environment variables set up successfully!");
'@
Create-File -path "$rootDir/scripts/setup-env.js" -content $setupEnvContent

Log-Success "OMEGA UI project structure created successfully!"
Write-Host ""
Write-Host "$Yellow Next steps:$Reset"
Write-Host "1. cd $rootDir"
Write-Host "2. npm install (or yarn install)"
Write-Host "3. npm run dev"
Write-Host ""
Write-Host "$Green Happy coding, OMEGA builder!$Reset"