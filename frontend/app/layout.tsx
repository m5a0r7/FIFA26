import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "FIFA 2026 Agent",
  description: "Football intelligence agent with explainable predictions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
