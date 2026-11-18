import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Student OS",
  description: "An MCP-powered AI coordination layer for student life.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
