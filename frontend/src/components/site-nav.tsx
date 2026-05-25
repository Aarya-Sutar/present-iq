"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { usePopup } from "@/components/popup";
import { useAuthStore } from "@/store/useAuthStore";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
];

export default function SiteNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { confirm } = usePopup();
  const token = useAuthStore((state) => state.token);
  const hydrateToken = useAuthStore((state) => state.hydrateToken);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    hydrateToken();
  }, [hydrateToken]);

  const handleLogout = async () => {
    const confirmed = await confirm({
      title: "Log out of DeckLens?",
      message:
        "You will be signed out of this session and returned to the login screen.",
      tone: "warning",
      confirmLabel: "Log out",
      cancelLabel: "Stay signed in",
    });

    if (!confirmed) return;

    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-white">
          DeckLens
        </Link>

        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-2">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "rounded-full px-4 py-2 text-sm transition",
                    "cursor-pointer",
                    active
                      ? "bg-white text-black"
                      : "text-zinc-300 hover:bg-zinc-900 hover:text-white",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-zinc-200 to-zinc-500 text-sm font-semibold text-zinc-950">
              U
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-white">
                {token ? "Signed in" : "Guest"}
              </p>
              <p className="text-xs text-zinc-400">
                {token ? "Profile access enabled" : "Log in to save work"}
              </p>
            </div>

            {token ? (
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-full border border-zinc-700 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800 hover:text-white"
              >
                Logout
              </button>
            ) : (
              <Link
                href="/login"
                className="rounded-full border border-zinc-700 px-3 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800 hover:text-white"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}