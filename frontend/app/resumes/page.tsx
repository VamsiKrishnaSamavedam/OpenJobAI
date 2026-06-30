"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { deleteResume, getResumes } from "@/lib/api";

type ResumeSummary = {
  id: number;
  filename: string;
  created_at: string;
  text_length: number;
  text_preview: string;
  extracted_skills: string[];
  skills_count: number;
};

const SELECTED_RESUME_STORAGE_KEY = "openjobai_selected_resume_id";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [activeResumeId, setActiveResumeId] = useState<string>("");
  const [expandedResumeId, setExpandedResumeId] = useState<number | null>(null);
  const [deletingResumeId, setDeletingResumeId] = useState<number | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function loadResumes() {
    try {
      setIsLoading(true);
      setError("");
      setMessage("");

      const data = await getResumes();
      const cleanedResumes = Array.isArray(data) ? data : [];

      setResumes(cleanedResumes);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load resumes.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  function setResumeAsActive(resumeId: number) {
    const resumeIdValue = String(resumeId);

    localStorage.setItem(SELECTED_RESUME_STORAGE_KEY, resumeIdValue);
    localStorage.setItem("latest_resume_id", resumeIdValue);

    setActiveResumeId(resumeIdValue);
    setMessage(`Resume ID ${resumeIdValue} is now selected as active resume.`);
    setError("");
  }

  async function handleDeleteResume(resumeId: number, filename: string) {
    const confirmed = window.confirm(
      `Are you sure you want to delete this resume?\n\n${filename}`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingResumeId(resumeId);
      setError("");
      setMessage("");

      await deleteResume(resumeId);

      setResumes((currentResumes) =>
        currentResumes.filter((resume) => resume.id !== resumeId)
      );

      if (String(resumeId) === activeResumeId) {
        localStorage.removeItem(SELECTED_RESUME_STORAGE_KEY);
        localStorage.removeItem("latest_resume_id");
        setActiveResumeId("");
      }

      setMessage(`Resume ID ${resumeId} deleted successfully.`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to delete resume.");
      }
    } finally {
      setDeletingResumeId(null);
    }
  }

  function formatDate(value: string | null | undefined) {
    if (!value) {
      return "Not available";
    }

    const parsedDate = new Date(value);

    if (Number.isNaN(parsedDate.getTime())) {
      return value;
    }

    return parsedDate.toLocaleString();
  }

  function formatNumber(value: number | null | undefined) {
    if (value === null || value === undefined) {
      return "N/A";
    }

    return value.toLocaleString();
  }

  function getResumeInitial(filename: string) {
    if (!filename) {
      return "CV";
    }

    const cleanName = filename.replace(/\.[^/.]+$/, "").trim();

    if (!cleanName) {
      return "CV";
    }

    return cleanName.slice(0, 2).toUpperCase();
  }

  function getSkillList(resume: ResumeSummary) {
    if (!Array.isArray(resume.extracted_skills)) {
      return [];
    }

    return resume.extracted_skills.filter((skill) => String(skill).trim());
  }

  useEffect(() => {
    const storedResumeId =
      localStorage.getItem(SELECTED_RESUME_STORAGE_KEY) ||
      localStorage.getItem("latest_resume_id");

    if (storedResumeId) {
      setActiveResumeId(storedResumeId);
    }

    loadResumes();
  }, []);

  const totalSkills = useMemo(() => {
    return resumes.reduce((total, resume) => {
      return total + getSkillList(resume).length;
    }, 0);
  }, [resumes]);

  const latestResume = resumes.length > 0 ? resumes[0] : null;

  const activeResume = resumes.find(
    (resume) => String(resume.id) === activeResumeId
  );

  return (
    <AppShell
      badge="Resume Center"
      title="Manage resumes used for AI job matching."
      subtitle="Review uploaded resumes, inspect extracted skills, and choose the active resume used for Jobs, Matches, ATS scoring, and XGBoost ranking."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/upload-resume"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
          >
            Upload New Resume
          </Link>

          <Link
            href="/jobs"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            Search Jobs
          </Link>
        </div>
      }
    >
      <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Total Resumes
          </p>

          <p className="mt-2 text-3xl font-black text-cyan-300">
            {resumes.length}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Candidate profiles uploaded
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Active Resume
          </p>

          <p className="mt-2 truncate text-3xl font-black text-purple-300">
            {activeResumeId ? `ID ${activeResumeId}` : "None"}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Used for scoring and matching
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Latest Resume
          </p>

          <p className="mt-2 text-3xl font-black text-emerald-300">
            {latestResume ? `ID ${latestResume.id}` : "N/A"}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Most recent loaded resume
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Extracted Skills
          </p>

          <p className="mt-2 text-3xl font-black text-amber-300">
            {formatNumber(totalSkills)}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Total skills across resumes
          </p>
        </div>
      </section>

      <section className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/20 backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-2xl font-black">Resume Library</h2>

            <p className="mt-1 text-sm text-slate-400">
              Select the resume that should be used for job scoring and match
              ranking.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={loadResumes}
              disabled={isLoading}
              className="rounded-2xl bg-slate-800 px-5 py-3 text-sm font-black hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? "Refreshing..." : "Refresh Resumes"}
            </button>

            <Link
              href="/upload-resume"
              className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 hover:bg-cyan-300"
            >
              Upload Resume
            </Link>
          </div>
        </div>

        {activeResume && (
          <div className="mt-5 rounded-2xl border border-emerald-800 bg-emerald-950/40 p-4 text-sm text-emerald-300">
            Active resume selected:{" "}
            <span className="font-black">
              ID {activeResume.id} · {activeResume.filename}
            </span>
          </div>
        )}

        {!activeResumeId && (
          <div className="mt-5 rounded-2xl border border-amber-800 bg-amber-950/40 p-4 text-sm text-amber-300">
            No active resume selected. Choose a resume below before using Jobs
            and Matches.
          </div>
        )}

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
              className="h-52 animate-pulse rounded-[2rem] border border-slate-800 bg-slate-900/70"
            />
          ))}
        </div>
      )}

      {!isLoading && resumes.length === 0 && (
        <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-10 text-center shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-2xl font-black">No resumes uploaded yet</p>

          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">
            Upload a resume first. OpenJobAI will extract text, detect skills,
            generate embeddings, and make it available for ATS scoring.
          </p>

          <div className="mt-6">
            <Link
              href="/upload-resume"
              className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 hover:bg-cyan-300"
            >
              Upload Resume
            </Link>
          </div>
        </div>
      )}

      {!isLoading && resumes.length > 0 && (
        <div className="grid gap-5">
          {resumes.map((resume) => {
            const isActive = String(resume.id) === activeResumeId;
            const isExpanded = expandedResumeId === resume.id;
            const skills = getSkillList(resume);
            const visibleSkills = isExpanded ? skills : skills.slice(0, 18);

            return (
              <article
                key={resume.id}
                className={`group rounded-[2rem] border p-6 shadow-xl shadow-black/10 backdrop-blur transition ${
                  isActive
                    ? "border-cyan-500/40 bg-cyan-500/10"
                    : "border-slate-800 bg-slate-950/85 hover:border-cyan-500/40"
                }`}
              >
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
                  <div className="min-w-0">
                    <div className="mb-4 flex flex-wrap items-center gap-3">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400 text-lg font-black text-slate-950">
                        {getResumeInitial(resume.filename)}
                      </div>

                      <div className="min-w-0">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
                            Resume ID: {resume.id}
                          </span>

                          {isActive && (
                            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-emerald-300">
                              Active
                            </span>
                          )}

                          <span className="rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-purple-300">
                            {skills.length} skills
                          </span>
                        </div>

                        <h3 className="truncate text-2xl font-black leading-snug text-white group-hover:text-cyan-100">
                          {resume.filename || `Resume ${resume.id}`}
                        </h3>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Uploaded
                        </p>

                        <p className="mt-2 text-sm text-slate-300">
                          {formatDate(resume.created_at)}
                        </p>
                      </div>

                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Text Length
                        </p>

                        <p className="mt-2 text-sm text-slate-300">
                          {formatNumber(resume.text_length)} characters
                        </p>
                      </div>

                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Skills Count
                        </p>

                        <p className="mt-2 text-sm text-slate-300">
                          {formatNumber(skills.length)} extracted skills
                        </p>
                      </div>
                    </div>

                    {resume.text_preview && (
                      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Resume Preview
                        </p>

                        <p className="mt-2 text-sm leading-6 text-slate-400">
                          {resume.text_preview}
                          {resume.text_preview.length >= 250 ? "..." : ""}
                        </p>
                      </div>
                    )}

                    <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                            Extracted Skills
                          </p>

                          <p className="mt-1 text-sm text-slate-400">
                            Used for skill overlap, ATS scoring, and match
                            ranking.
                          </p>
                        </div>

                        {skills.length > 18 && (
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedResumeId(isExpanded ? null : resume.id)
                            }
                            className="text-left text-xs font-bold text-cyan-300 hover:text-cyan-200 md:text-right"
                          >
                            {isExpanded ? "Show fewer" : "Show all skills"}
                          </button>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {visibleSkills.length > 0 ? (
                          visibleSkills.map((skill, index) => (
                            <span
                              key={`${resume.id}-${skill}-${index}`}
                              className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-300 ring-1 ring-cyan-500/30"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <p className="text-sm text-slate-500">
                            No skills extracted.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <aside className="flex flex-col gap-3">
                    <div className="rounded-[2rem] border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        Resume Status
                      </p>

                      <p
                        className={`mt-2 text-2xl font-black ${
                          isActive ? "text-emerald-300" : "text-slate-300"
                        }`}
                      >
                        {isActive ? "Active" : "Available"}
                      </p>

                      <p className="mt-2 text-xs leading-5 text-slate-500">
                        {isActive
                          ? "This resume is used for scoring jobs and generating matches."
                          : "Select this resume to use it for Jobs and Matches."}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setResumeAsActive(resume.id)}
                      disabled={isActive}
                      className={`rounded-2xl px-4 py-3 text-sm font-black disabled:cursor-not-allowed disabled:opacity-70 ${
                        isActive
                          ? "border border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                          : "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
                      }`}
                    >
                      {isActive ? "Active Resume" : "Set as Active"}
                    </button>

                    <Link
                      href="/jobs"
                      onClick={() => setResumeAsActive(resume.id)}
                      className="rounded-2xl border border-slate-700 px-4 py-3 text-center text-sm font-black hover:bg-slate-800"
                    >
                      Use for Job Search
                    </Link>

                    <Link
                      href="/matches"
                      onClick={() => setResumeAsActive(resume.id)}
                      className="rounded-2xl border border-slate-700 px-4 py-3 text-center text-sm font-black hover:bg-slate-800"
                    >
                      Use for Matches
                    </Link>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteResume(resume.id, resume.filename)
                      }
                      disabled={deletingResumeId === resume.id}
                      className="rounded-2xl border border-rose-800 bg-rose-950/40 px-4 py-3 text-sm font-black text-rose-300 hover:bg-rose-900 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {deletingResumeId === resume.id
                        ? "Deleting..."
                        : "Delete Resume"}
                    </button>
                  </aside>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}