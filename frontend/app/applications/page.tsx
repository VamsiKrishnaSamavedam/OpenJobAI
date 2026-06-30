"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import {
  deleteApplication,
  getApplications,
  updateApplicationStatus,
} from "@/lib/api";

type Application = {
  application_id: number;
  job_id: number;
  status: string;
  notes: string | null;
  applied_at: string | null;
  created_at: string;
  title: string | null;
  company: string | null;
  location: string | null;
  apply_url: string | null;
  source: string | null;
};

const STATUS_OPTIONS = ["saved", "applied", "interviewing", "rejected", "offer"];

function getStatusBadgeClass(status: string) {
  if (status === "offer") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  }

  if (status === "interviewing") {
    return "border-purple-500/40 bg-purple-500/10 text-purple-300";
  }

  if (status === "applied") {
    return "border-cyan-500/40 bg-cyan-500/10 text-cyan-300";
  }

  if (status === "rejected") {
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }

  return "border-slate-600 bg-slate-800/80 text-slate-300";
}

function getStatusDotClass(status: string) {
  if (status === "offer") {
    return "bg-emerald-400";
  }

  if (status === "interviewing") {
    return "bg-purple-400";
  }

  if (status === "applied") {
    return "bg-cyan-400";
  }

  if (status === "rejected") {
    return "bg-rose-400";
  }

  return "bg-slate-400";
}

function getSourceLabel(source: string | null) {
  const value = (source || "").toLowerCase();

  if (value.includes("linkedin")) {
    return "LinkedIn";
  }

  if (value.includes("indeed")) {
    return "Indeed";
  }

  if (value.includes("remote")) {
    return "RemoteOK";
  }

  return source || "Unknown";
}

function getSafeApplyUrl(applyUrl: string | null) {
  if (!applyUrl) {
    return "";
  }

  if (applyUrl.startsWith("http://") || applyUrl.startsWith("https://")) {
    return applyUrl;
  }

  if (applyUrl.startsWith("www.")) {
    return `https://${applyUrl}`;
  }

  if (applyUrl.startsWith("/")) {
    return `https://remoteok.com${applyUrl}`;
  }

  return applyUrl;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not available";
  }

  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return parsedDate.toLocaleString();
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function loadApplications() {
    try {
      setIsLoading(true);
      setError("");
      setMessage("");

      const data = await getApplications(100);

      setApplications(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load applications.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStatusChange(
    applicationId: number,
    newStatus: string,
    currentNotes: string | null
  ) {
    try {
      setUpdatingId(applicationId);
      setError("");
      setMessage("");

      await updateApplicationStatus(
        applicationId,
        newStatus,
        currentNotes || ""
      );

      setMessage(`Application ${applicationId} updated to ${newStatus}.`);

      await loadApplications();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to update application.");
      }
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDeleteApplication(applicationId: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this application from the tracker?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setUpdatingId(applicationId);
      setError("");
      setMessage("");

      await deleteApplication(applicationId);

      setMessage(`Application ${applicationId} deleted successfully.`);

      await loadApplications();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to delete application.");
      }
    } finally {
      setUpdatingId(null);
    }
  }

  useEffect(() => {
    loadApplications();
  }, []);

  const filteredApplications = useMemo(() => {
    if (statusFilter === "all") {
      return applications;
    }

    return applications.filter(
      (application) => application.status === statusFilter
    );
  }, [applications, statusFilter]);

  const savedCount = applications.filter(
    (application) => application.status === "saved"
  ).length;

  const appliedCount = applications.filter(
    (application) => application.status === "applied"
  ).length;

  const interviewingCount = applications.filter(
    (application) => application.status === "interviewing"
  ).length;

  const offerCount = applications.filter(
    (application) => application.status === "offer"
  ).length;

  return (
    <AppShell
      badge="Application Pipeline"
      title="Track every opportunity from saved to offer."
      subtitle="Manage saved jobs, update application stages, open job postings, and keep your job search pipeline organized in one place."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={loadApplications}
            disabled={isLoading}
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? "Loading..." : "Refresh"}
          </button>

          <Link
            href="/jobs"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            Search Jobs
          </Link>
        </div>
      }
    >
      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Total
          </p>
          <p className="mt-2 text-3xl font-black">{applications.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Applied
          </p>
          <p className="mt-2 text-3xl font-black text-cyan-300">
            {appliedCount}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Interviewing
          </p>
          <p className="mt-2 text-3xl font-black text-purple-300">
            {interviewingCount}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Offers
          </p>
          <p className="mt-2 text-3xl font-black text-emerald-300">
            {offerCount}
          </p>
        </div>
      </section>

      <section className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/20 backdrop-blur">
        <div className="grid gap-3 md:grid-cols-6">
          <button
            type="button"
            onClick={() => setStatusFilter("all")}
            className={`rounded-2xl border px-4 py-4 text-left transition ${
              statusFilter === "all"
                ? "border-cyan-500/40 bg-cyan-500/10"
                : "border-slate-800 bg-slate-900/70 hover:border-slate-700"
            }`}
          >
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">
              All
            </p>
            <p className="mt-2 text-2xl font-black">{applications.length}</p>
          </button>

          {STATUS_OPTIONS.map((status) => {
            const count = applications.filter(
              (application) => application.status === status
            ).length;

            return (
              <button
                key={status}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={`rounded-2xl border px-4 py-4 text-left transition ${
                  statusFilter === status
                    ? "border-cyan-500/40 bg-cyan-500/10"
                    : "border-slate-800 bg-slate-900/70 hover:border-slate-700"
                }`}
              >
                <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                  {status}
                </p>
                <p className="mt-2 text-2xl font-black">{count}</p>
              </button>
            );
          })}
        </div>

        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-black">Tracked Applications</h2>

            <p className="mt-1 text-sm text-slate-400">
              Showing {filteredApplications.length} of {applications.length}{" "}
              applications.
            </p>
          </div>
        </div>

        {message && (
          <div className="mt-5 rounded-2xl border border-emerald-800 bg-emerald-950/40 p-4 text-sm text-emerald-300">
            {message}
          </div>
        )}

        {error && (
          <div className="mt-5 rounded-2xl border border-rose-800 bg-rose-950 p-4 text-sm text-rose-300">
            {error}
          </div>
        )}
      </section>

      {isLoading && (
        <div className="grid gap-4">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="h-44 animate-pulse rounded-[2rem] border border-slate-800 bg-slate-900/70"
            />
          ))}
        </div>
      )}

      {!isLoading && filteredApplications.length === 0 && (
        <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-10 text-center shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-2xl font-black">
            {applications.length === 0
              ? "No applications saved yet"
              : "No applications match this filter"}
          </p>

          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">
            Save jobs from the Jobs or Matches page, then manage your
            application progress here.
          </p>

          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <Link
              href="/jobs"
              className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 hover:bg-cyan-300"
            >
              Search Jobs
            </Link>

            <Link
              href="/matches"
              className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm font-black hover:bg-slate-800"
            >
              View Matches
            </Link>
          </div>
        </div>
      )}

      {!isLoading && filteredApplications.length > 0 && (
        <div className="grid gap-5">
          {filteredApplications.map((application) => (
            <article
              key={application.application_id}
              className="group rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/10 backdrop-blur transition hover:border-cyan-500/40"
            >
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_280px]">
                <div className="min-w-0">
                  <div className="mb-3 flex flex-wrap items-center gap-3">
                    <span
                      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wide ${getStatusBadgeClass(
                        application.status
                      )}`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${getStatusDotClass(
                          application.status
                        )}`}
                      />
                      {application.status}
                    </span>

                    <span className="rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
                      Application ID: {application.application_id}
                    </span>

                    <span className="rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
                      Job ID: {application.job_id}
                    </span>

                    <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-cyan-300">
                      {getSourceLabel(application.source)}
                    </span>
                  </div>

                  <h3 className="text-2xl font-black leading-snug text-white group-hover:text-cyan-100">
                    {application.title || "Untitled Job"}
                  </h3>

                  <p className="mt-2 text-sm font-semibold text-slate-300">
                    {application.company || "Unknown Company"} ·{" "}
                    {application.location || "Unknown Location"}
                  </p>

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        Saved At
                      </p>
                      <p className="mt-2 text-sm text-slate-300">
                        {formatDate(application.created_at)}
                      </p>
                    </div>

                    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        Applied At
                      </p>
                      <p className="mt-2 text-sm text-slate-300">
                        {formatDate(application.applied_at)}
                      </p>
                    </div>
                  </div>

                  {application.notes && (
                    <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        Notes
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        {application.notes}
                      </p>
                    </div>
                  )}
                </div>

                <aside className="flex flex-col gap-3">
                  <div className="rounded-[2rem] border border-slate-800 bg-slate-900/70 p-4">
                    <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
                      Update Status
                    </label>

                    <select
                      value={application.status}
                      disabled={updatingId === application.application_id}
                      onChange={(event) =>
                        handleStatusChange(
                          application.application_id,
                          event.target.value,
                          application.notes
                        )
                      }
                      className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>

                    <p className="mt-3 text-xs leading-5 text-slate-500">
                      Move this job through your application pipeline.
                    </p>
                  </div>

                  {application.apply_url && (
                    <a
                      href={getSafeApplyUrl(application.apply_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-2xl border border-slate-700 px-4 py-3 text-center text-sm font-black hover:bg-slate-800"
                    >
                      Open Job
                    </a>
                  )}

                  <button
                    type="button"
                    onClick={() =>
                      handleDeleteApplication(application.application_id)
                    }
                    disabled={updatingId === application.application_id}
                    className="rounded-2xl border border-rose-800 bg-rose-950/40 px-4 py-3 text-sm font-black text-rose-300 hover:bg-rose-900 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {updatingId === application.application_id
                      ? "Updating..."
                      : "Delete"}
                  </button>
                </aside>
              </div>
            </article>
          ))}
        </div>
      )}
    </AppShell>
  );
}