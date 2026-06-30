"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  title: string;
  subtitle?: string;
  badge?: string;
  actions?: ReactNode;
};

const navItems = [
  {
    label: "Dashboard",
    href: "/",
    short: "DB",
    description: "Overview",
  },
  {
    label: "Resumes",
    href: "/resumes",
    short: "CV",
    description: "Resume center",
  },
  {
    label: "Upload Resume",
    href: "/upload-resume",
    short: "UP",
    description: "New resume",
  },
  {
    label: "Jobs",
    href: "/jobs",
    short: "JB",
    description: "Live search",
  },
  {
    label: "Matches",
    href: "/matches",
    short: "AI",
    description: "AI ranking",
  },
  {
    label: "Applications",
    href: "/applications",
    short: "AP",
    description: "Tracker",
  },
];

export default function AppShell({
  children,
  title,
  subtitle,
  badge,
  actions,
}: AppShellProps) {
  const pathname = usePathname();

  function isActiveRoute(href: string) {
    if (href === "/") {
      return pathname === "/";
    }

    return pathname.startsWith(href);
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,#0f766e33,transparent_35%),radial-gradient(circle_at_top_right,#7c3aed33,transparent_32%),linear-gradient(180deg,#020617_0%,#0f172a_100%)] text-white">
      <div className="mx-auto flex min-h-screen max-w-[1500px] gap-6 px-4 py-4 lg:px-6 lg:py-6">
        <aside className="hidden w-72 shrink-0 lg:block">
          <div className="sticky top-6 flex h-[calc(100vh-3rem)] flex-col rounded-[2rem] border border-slate-800 bg-slate-950/85 p-4 shadow-2xl shadow-black/30 backdrop-blur">
            <Link
              href="/"
              className="mb-6 flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/80 p-4"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400 text-lg font-black text-slate-950 shadow-lg shadow-cyan-500/20">
                OJ
              </div>

              <div>
                <p className="text-lg font-black tracking-tight">OpenJobAI</p>
                <p className="text-xs text-slate-400">
                  AI Job Platform
                </p>
              </div>
            </Link>

            <nav className="space-y-2">
              {navItems.map((item) => {
                const active = isActiveRoute(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`group flex items-center gap-3 rounded-2xl border px-4 py-3 transition ${
                      active
                        ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-200"
                        : "border-transparent text-slate-300 hover:border-slate-700 hover:bg-slate-900"
                    }`}
                  >
                    <span
                      className={`flex h-10 w-10 items-center justify-center rounded-xl text-xs font-black ${
                        active
                          ? "bg-cyan-400 text-slate-950"
                          : "bg-slate-800 text-slate-300 group-hover:bg-slate-700"
                      }`}
                    >
                      {item.short}
                    </span>

                    <span>
                      <span className="block text-sm font-black">
                        {item.label}
                      </span>
                      <span className="block text-xs text-slate-500">
                        {item.description}
                      </span>
                    </span>
                  </Link>
                );
              })}
            </nav>

            <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">
                System
              </p>

              <p className="mt-3 text-sm font-bold text-slate-200">
                FastAPI + Next.js
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                PostgreSQL, Apify, embeddings, ATS scoring, and XGBoost ranking.
              </p>
            </div>
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <header className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur lg:hidden">
            <div className="mb-4 flex items-center justify-between gap-4">
              <Link href="/" className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-400 text-lg font-black text-slate-950">
                  OJ
                </div>

                <div>
                  <p className="font-black">OpenJobAI</p>
                  <p className="text-xs text-slate-400">AI Job Platform</p>
                </div>
              </Link>
            </div>

            <nav className="flex gap-2 overflow-x-auto pb-1">
              {navItems.map((item) => {
                const active = isActiveRoute(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`shrink-0 rounded-xl border px-3 py-2 text-xs font-bold ${
                      active
                        ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                        : "border-slate-700 bg-slate-900 text-slate-300"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </header>

          <div className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                {badge && (
                  <span className="mb-4 inline-flex rounded-full border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
                    {badge}
                  </span>
                )}

                <h1 className="text-3xl font-black tracking-tight md:text-5xl">
                  {title}
                </h1>

                {subtitle && (
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 md:text-base">
                    {subtitle}
                  </p>
                )}
              </div>

              {actions && <div className="shrink-0">{actions}</div>}
            </div>
          </div>

          {children}
        </section>
      </div>
    </main>
  );
}