"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { checkHealth, getDashboardStats } from "@/lib/api";

type StatusType = "online" | "offline" | "checking" | "connected" | "unknown";

type DashboardStats = {
  total_resumes: number;
  total_jobs: number;
  total_applications: number;
  total_feedback: number;
  latest_resume_id: number | null;
  xgb_model_trained: boolean;
};

export default function HomePage() {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [databaseStatus, setDatabaseStatus] = useState<string>("Checking...");
  const [activeResumeId, setActiveResumeId] = useState<string>("");
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(
    null
  );
  const [statsError, setStatsError] = useState<string>("");

  useEffect(() => {
    async function loadHealth() {
      try {
        const data = await checkHealth();

        setBackendStatus(data.status || "online");
        setDatabaseStatus(data.database_connected ? "connected" : "not connected");
      } catch (error) {
        setBackendStatus("offline");
        setDatabaseStatus("unknown");
      }
    }

    async function loadDashboardStats() {
      try {
        setStatsError("");

        const data = await getDashboardStats();

        setDashboardStats(data);

        if (data.latest_resume_id) {
          setActiveResumeId(String(data.latest_resume_id));
        }
      } catch (error) {
        setStatsError("Dashboard stats are not available yet.");
        setDashboardStats(null);
      }
    }

    const storedResumeId = localStorage.getItem("openjobai_selected_resume_id");

    if (storedResumeId) {
      setActiveResumeId(storedResumeId);
    }

    loadHealth();
    loadDashboardStats();
  }, []);

  function getStatusType(value: string): StatusType {
    const normalizedValue = value.toLowerCase();

    if (normalizedValue.includes("checking")) {
      return "checking";
    }

    if (
      normalizedValue.includes("ok") ||
      normalizedValue.includes("online") ||
      normalizedValue.includes("healthy") ||
      normalizedValue.includes("connected")
    ) {
      return "connected";
    }

    if (
      normalizedValue.includes("offline") ||
      normalizedValue.includes("not connected")
    ) {
      return "offline";
    }

    return "unknown";
  }

  function getStatusClass(value: string) {
    const statusType = getStatusType(value);

    if (statusType === "connected") {
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
    }

    if (statusType === "checking") {
      return "border-cyan-500/40 bg-cyan-500/10 text-cyan-300";
    }

    if (statusType === "offline") {
      return "border-rose-500/40 bg-rose-500/10 text-rose-300";
    }

    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  }

  function formatStat(value: number | null | undefined) {
    if (value === null || value === undefined) {
      return "N/A";
    }

    return value.toLocaleString();
  }

  const workflowSteps = [
    {
      step: "01",
      title: "Upload Resume",
      description:
        "Parse your resume, extract skills, and prepare your profile for job matching.",
    },
    {
      step: "02",
      title: "Search Jobs",
      description:
        "Fetch fresh jobs from LinkedIn and Indeed using live Apify-powered search.",
    },
    {
      step: "03",
      title: "Score Matches",
      description:
        "Compare every job with your resume using ATS compatibility and semantic similarity.",
    },
    {
      step: "04",
      title: "Track Applications",
      description:
        "Save jobs, manage application status, and collect feedback for better ranking.",
    },
  ];

  const featureCards = [
    {
      title: "ATS Compatibility",
      value: "Resume-job fit",
      description:
        "Scores jobs using skills, semantic similarity, experience, education, and location signals.",
    },
    {
      title: "XGBoost Ranking",
      value: dashboardStats?.xgb_model_trained ? "Model trained" : "Needs data",
      description:
        "Learns from your feedback to improve future job recommendations.",
    },
    {
      title: "Live Job Fetching",
      value: "LinkedIn + Indeed",
      description:
        "Searches new jobs dynamically instead of only filtering saved database jobs.",
    },
  ];

  return (
    <AppShell
      badge="AI-Powered Job Search"
      title="Find better jobs with resume-aware AI recommendations."
      subtitle="OpenJobAI helps you upload a resume, fetch fresh jobs, score each role using ATS-style compatibility, and prioritize the best opportunities using your own feedback-trained ranking model."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/jobs"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
          >
            Search Jobs
          </Link>

          <Link
            href="/upload-resume"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            Upload Resume
          </Link>
        </div>
      }
    >
      <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Resumes
          </p>

          <p className="mt-2 text-3xl font-black text-cyan-300">
            {formatStat(dashboardStats?.total_resumes)}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Uploaded candidate profiles
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Saved Jobs
          </p>

          <p className="mt-2 text-3xl font-black text-purple-300">
            {formatStat(dashboardStats?.total_jobs)}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Jobs stored in PostgreSQL
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Applications
          </p>

          <p className="mt-2 text-3xl font-black text-emerald-300">
            {formatStat(dashboardStats?.total_applications)}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Jobs in your tracker
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Feedback Records
          </p>

          <p className="mt-2 text-3xl font-black text-amber-300">
            {formatStat(dashboardStats?.total_feedback)}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Used for XGBoost learning
          </p>
        </div>
      </section>

      {statsError && (
        <div className="mb-6 rounded-2xl border border-amber-800 bg-amber-950/40 p-4 text-sm text-amber-300">
          {statsError} Make sure the backend endpoint{" "}
          <span className="font-mono">/dashboard/stats</span> is added and the
          backend server is running.
        </div>
      )}

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <div className="mb-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
              ATS + ML Ranking
            </span>

            <span className="rounded-full border border-purple-500/40 bg-purple-500/10 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-purple-300">
              Live Job Search
            </span>

            <span
              className={`rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.2em] ${
                dashboardStats?.xgb_model_trained
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                  : "border-amber-500/40 bg-amber-500/10 text-amber-300"
              }`}
            >
              {dashboardStats?.xgb_model_trained
                ? "XGBoost Trained"
                : "XGBoost Pending"}
            </span>
          </div>

          <h2 className="text-3xl font-black">
            Complete AI job matching workflow
          </h2>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Your platform now supports resume upload, live job fetching, scoring,
            personalized ranking, feedback learning, and application tracking.
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {featureCards.map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
              >
                <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">
                  {feature.title}
                </p>

                <p className="mt-3 text-2xl font-black text-cyan-300">
                  {feature.value}
                </p>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        <aside className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-sm font-black uppercase tracking-[0.2em] text-slate-500">
            System Status
          </p>

          <div className="mt-5 space-y-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">Backend API</p>

                  <p className="mt-1 text-2xl font-black">{backendStatus}</p>
                </div>

                <span
                  className={`rounded-full border px-3 py-1 text-xs font-bold ${getStatusClass(
                    backendStatus
                  )}`}
                >
                  {getStatusType(backendStatus)}
                </span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">PostgreSQL</p>

                  <p className="mt-1 text-2xl font-black">{databaseStatus}</p>
                </div>

                <span
                  className={`rounded-full border px-3 py-1 text-xs font-bold ${getStatusClass(
                    databaseStatus
                  )}`}
                >
                  {getStatusType(databaseStatus)}
                </span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-sm text-slate-400">Selected Resume</p>

              <p className="mt-1 text-2xl font-black">
                {activeResumeId ? `ID ${activeResumeId}` : "Not selected"}
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Select a resume before searching jobs to enable ATS and ML
                recommendation scores.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-sm text-slate-400">Latest Resume in DB</p>

              <p className="mt-1 text-2xl font-black">
                {dashboardStats?.latest_resume_id
                  ? `ID ${dashboardStats.latest_resume_id}`
                  : "N/A"}
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Latest resume saved in PostgreSQL.
              </p>
            </div>
          </div>
        </aside>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-cyan-300">
            Quick Actions
          </p>

          <h2 className="mt-3 text-3xl font-black">Start your workflow</h2>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Use these shortcuts to move through the full job recommendation
            pipeline.
          </p>

          <div className="mt-6 grid gap-3">
            <Link
              href="/upload-resume"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-4 hover:border-cyan-500/40"
            >
              <p className="font-black">Upload or manage resume</p>
              <p className="mt-1 text-sm text-slate-400">
                Add a resume and extract skills for matching.
              </p>
            </Link>

            <Link
              href="/jobs"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-4 hover:border-cyan-500/40"
            >
              <p className="font-black">Search live jobs</p>
              <p className="mt-1 text-sm text-slate-400">
                Fetch jobs dynamically from LinkedIn and Indeed.
              </p>
            </Link>

            <Link
              href="/matches"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-4 hover:border-cyan-500/40"
            >
              <p className="font-black">Review ranked matches</p>
              <p className="mt-1 text-sm text-slate-400">
                Compare recommended, ATS, semantic, and skill scores.
              </p>
            </Link>

            <Link
              href="/applications"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-4 hover:border-cyan-500/40"
            >
              <p className="font-black">Track applications</p>
              <p className="mt-1 text-sm text-slate-400">
                Save jobs and monitor your application progress.
              </p>
            </Link>
          </div>
        </div>

        <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-purple-300">
            Matching Pipeline
          </p>

          <h2 className="mt-3 text-3xl font-black">
            Resume to ranked job recommendations
          </h2>

          <div className="mt-6 grid gap-4">
            {workflowSteps.map((item) => (
              <div
                key={item.step}
                className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-4 md:grid-cols-[70px_1fr]"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400 text-lg font-black text-slate-950">
                  {item.step}
                </div>

                <div>
                  <p className="text-lg font-black">{item.title}</p>

                  <p className="mt-1 text-sm leading-6 text-slate-400">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </AppShell>
  );
}