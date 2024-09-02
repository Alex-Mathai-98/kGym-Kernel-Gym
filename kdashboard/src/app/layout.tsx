import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { DashboardNav } from "@/app/components/nav"
import { Suspense } from "react";
import { Skeleton } from "@nextui-org/react";

export const metadata: Metadata = {
  title: "KBDr Dashboard",
  description: "Monitoring and Managing KBDr Jobs",
};

export default async function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body lang='en'>
        <Providers>
          <main className="light text-foreground bg-background">
            <DashboardNav />
            <div className="container mx-auto max-w-4xl flex-grow mt-6 flex-col">
              {children}
            </div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
