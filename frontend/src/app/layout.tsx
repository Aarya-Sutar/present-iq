import type { Metadata } from "next";
import "./globals.css";
import SiteNav from "@/components/site-nav";
import { PopupProvider } from "@/components/popup";

export const metadata: Metadata = {
  title: "DeckLens",
  description: "AI-powered contextual presentation evaluation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-zinc-950 text-white antialiased">
        <PopupProvider>
          <SiteNav />
          {children}
        </PopupProvider>
      </body>
    </html>
  );
}