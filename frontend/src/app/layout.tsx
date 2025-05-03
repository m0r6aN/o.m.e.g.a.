import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/providers/theme-provider";
import toast, { Toaster } from 'react-hot-toast';
import { QueryProvider } from "@/providers/query-provider";

const inter = Inter({ subsets: ["latin"] });

// https://react-hot-toast.com/docs/toast
const notify = () => toast('Here is your toast.');

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
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}