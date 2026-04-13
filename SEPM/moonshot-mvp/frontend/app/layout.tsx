import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SRM Moonshot SOC",
  description: "Zero Trust SOC dashboard MVP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-soc-bg text-soc-text antialiased">{children}</body>
    </html>
  );
}
