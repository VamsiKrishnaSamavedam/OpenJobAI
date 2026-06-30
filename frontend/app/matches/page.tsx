"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { matchResume, saveApplication, saveFeedback } from "@/lib/api";

type MatchJob = {
  job_id: number;
  id?: number;
  title: string | null;
  company: string | null;
  location: string | null;
  apply_url: string | null;
  source?: string | null;
  description?: string | null;

  final_score?: number;
  ats_score?: number;
  ats_compatibility_score?: number;
  semantic_score?: number;
  skill_score?: number;
  ml_preference_score?: number | null;
  recommended_score?: number;

  matched_skills?: string[];
  missing_skills?: string[];
  knockout_flags?: string[];
  ats_explanation?: string[];
};

const SELECTED_RESUME_STORAGE_KEY = "openjobai_selected_resume_id";

export default function MatchesPage() {
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [manualResumeId, setManualResumeId] = useState<string>("");
  const [matches, setMatches] = useState<MatchJob[]>([]);
  const [limit, setLimit] = useState<number>(20);

  const [isMatching, setIsMatching] = useState<boolean>(false);
  const [isTraining, setIsTraining] = useState<boolean>(false);

  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null);
  const [feedbackState, setFeedbackState] = useState<Record<number, string>>({});

  useEffect(() => {
    const selectedResumeId =
      localStorage.getItem(SELECTED_RESUME_STORAGE_KEY) ||
      localStorage.getItem("latest_resume_id");

    if (selectedResumeId) {
      const parsedResumeId = Number(selectedResumeId);

      if (parsedResumeId > 0) {
        setResumeId(parsedResumeId);
        setManualResumeId(String(parsedResumeId));
      }
    }
  }, []);

  function getJobId(match: MatchJob) {
    return match.job_id || match.id || 0;
  }

  function normalizeScore(score: number | null | undefined) {
    if (score === null || score === undefined) {
      return undefined;
    }

    const numericScore = Number(score);

    if (Number.isNaN(numericScore)) {
      return undefined;
    }

    if (numericScore <= 1) {
      return Math.round(numericScore * 100);
    }

    return Math.round(numericScore);
  }

  function formatScore(score: number | null | undefined) {
    const normalizedScore = normalizeScore(score);

    if (normalizedScore === undefined) {
      return "N/A";
    }

    return `${normalizedScore}%`;
  }

  function getRecommendedScore(match: MatchJob) {
    return (
      normalizeScore(match.recommended_score) ??
      normalizeScore(match.final_score) ??
      normalizeScore(match.ats_score)
    );
  }

  function getAtsScore(match: MatchJob) {
    return (
      normalizeScore(match.ats_compatibility_score) ??
      normalizeScore(match.ats_score) ??
      normalizeScore(match.final_score)
    );
  }

  function getSourceLabel(source: string | null | undefined) {
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

  function getRecommendationLabel(score: number | undefined) {
    if (score === undefined) {
      return "Not Scored";
    }

    if (score >= 75) {
      return "Strong Match";
    }

    if (score >= 60) {
      return "Good Match";
    }

    if (score >= 45) {
      return "Possible Match";
    }

    return "Low Match";
  }

  function getRecommendationClass(score: number | undefined) {
    if (score === undefined) {
      return "border-slate-700 bg-slate-900 text-slate-300";
    }

    if (score >= 75) {
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
    }

    if (score >= 60) {
      return "border-cyan-500/40 bg-cyan-500/10 text-cyan-300";
    }

    if (score >= 45) {
      return "border-amber-500/40 bg-amber-500/10 text-amber-300";
    }

    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  }

  function getScoreBarClass(score: number | undefined) {
    if (score === undefined) {
      return "bg-slate-700";
    }

    if (score >= 75) {
      return "bg-emerald-400";
    }

    if (score >= 60) {
      return "bg-cyan-400";
    }

    if (score >= 45) {
      return "bg-amber-400";
    }

    return "bg-rose-400";
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

  function cleanDescription(description: string | null | undefined) {
    if (!description) {
      return "";
    }

    return description
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&nbsp;/g, " ")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, " ")
      .trim();
  }

  function getMatchInsight(match: MatchJob) {
    const recommendedScore = getRecommendedScore(match);
    const matchedSkills = match.matched_skills || [];
    const missingSkills = match.missing_skills || [];

    if (recommendedScore !== undefined && recommendedScore >= 75) {
      return "This role is a strong fit based on your resume, skills, and ranking model.";
    }

    if (matchedSkills.length > missingSkills.length) {
      return "This role has good skill overlap, but a few gaps may need attention.";
    }

    if (missingSkills.length > matchedSkills.length) {
      return "This role has several missing skills, so review requirements carefully before applying.";
    }

    return "Review the score breakdown and job description before deciding.";
  }

  async function handleRunMatching() {
    const selectedResumeId = Number(manualResumeId);

    if (!selectedResumeId || selectedResumeId <= 0) {
      setError("Please enter a valid resume ID.");
      return;
    }

    try {
      setIsMatching(true);
      setError("");
      setMessage("");
      setMatches([]);

      const data = await matchResume(selectedResumeId, limit);

      setResumeId(selectedResumeId);
      localStorage.setItem(SELECTED_RESUME_STORAGE_KEY, String(selectedResumeId));
      localStorage.setItem("latest_resume_id", String(selectedResumeId));

      const returnedMatches = Array.isArray(data) ? data : data.matches || [];

      const sortedMatches = [...returnedMatches].sort((first, second) => {
        const firstScore = getRecommendedScore(first) || 0;
        const secondScore = getRecommendedScore(second) || 0;

        return secondScore - firstScore;
      });

      setMatches(sortedMatches);
      setMessage(`Generated ${sortedMatches.length} ranked matches.`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to generate matches.");
      }
    } finally {
      setIsMatching(false);
    }
  }

  async function handleSaveApplication(jobId: number) {
    try {
      setError("");
      setMessage("");

      const data = await saveApplication(
        jobId,
        "saved",
        "Saved from OpenJobAI matches page."
      );

      setMessage(
        `Job ID ${jobId} saved to application tracker. Application ID: ${data.application_id}`
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save application.");
      }
    }
  }

  async function handleFeedback(jobId: number, feedbackLabel: string) {
    if (!resumeId) {
      setError("Resume ID is missing. Run matching first.");
      return;
    }

    try {
      setError("");
      setMessage("");

      await saveFeedback(resumeId, jobId, feedbackLabel);

      setFeedbackState((currentState) => ({
        ...currentState,
        [jobId]: feedbackLabel,
      }));

      setMessage(`Feedback saved: ${feedbackLabel} for Job ID ${jobId}.`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save feedback.");
      }
    }
  }

  async function handleRetrainModel() {
    try {
      setIsTraining(true);
      setError("");
      setMessage("");

      const response = await fetch("http://127.0.0.1:8000/ml/train-xgb-ranker", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to retrain XGBoost model.");
      }

      const data = await response.json();

      if (data.trained) {
        setMessage(
          `XGBoost model retrained successfully with ${data.training_rows} feedback records.`
        );
      } else {
        setMessage(
          `Model not trained yet: ${data.reason || "More feedback is needed."}`
        );
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to retrain model.");
      }
    } finally {
      setIsTraining(false);
    }
  }

  const topScore =
    matches.length > 0
      ? Math.max(...matches.map((match) => getRecommendedScore(match) || 0))
      : 0;

  const strongMatches = matches.filter((match) => {
    const score = getRecommendedScore(match) || 0;
    return score >= 75;
  }).length;

  const feedbackCount = Object.keys(feedbackState).length;

  return (
    <AppShell
      badge="AI Match Ranking"
      title="Rank saved jobs by your real resume fit."
      subtitle="Generate ranked matches using ATS compatibility, semantic similarity, skill overlap, and your feedback-trained XGBoost preference model."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/jobs"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
          >
            Search Jobs
          </Link>

          <Link
            href="/applications"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            Applications
          </Link>
        </div>
      }
    >
      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Active Resume
          </p>
          <p className="mt-2 text-3xl font-black text-cyan-300">
            {resumeId ? `ID ${resumeId}` : "None"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Matches
          </p>
          <p className="mt-2 text-3xl font-black">{matches.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Strong Matches
          </p>
          <p className="mt-2 text-3xl font-black text-emerald-300">
            {strongMatches}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Top Score
          </p>
          <p className="mt-2 text-3xl font-black text-purple-300">
            {topScore ? `${topScore}%` : "N/A"}
          </p>
        </div>
      </section>

      <section className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/20 backdrop-blur">
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto_auto]">
          <label className="block">
            <span className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Resume ID
            </span>

            <input
              type="number"
              min={1}
              value={manualResumeId}
              onChange={(event) => setManualResumeId(event.target.value)}
              placeholder="Example: 6"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Number of Matches
            </span>

            <select
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value={10}>10 matches</option>
              <option value={20}>20 matches</option>
              <option value={30}>30 matches</option>
              <option value={50}>50 matches</option>
              <option value={100}>100 matches</option>
            </select>
          </label>

          <button
            type="button"
            onClick={handleRunMatching}
            disabled={isMatching}
            className="rounded-2xl bg-cyan-400 px-6 py-3 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
          >
            {isMatching ? "Matching..." : "Run Matching"}
          </button>

          <button
            type="button"
            onClick={handleRetrainModel}
            disabled={isTraining}
            className="rounded-2xl bg-purple-500 px-6 py-3 text-sm font-black text-white shadow-lg shadow-purple-500/20 hover:bg-purple-400 disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
          >
            {isTraining ? "Training..." : "Retrain XGBoost"}
          </button>
        </div>

        {!manualResumeId && (
          <div className="mt-5 rounded-2xl border border-amber-800 bg-amber-950/40 p-4 text-sm text-amber-300">
            No active resume found. Upload a resume first or manually enter a
            resume ID.
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

      <section>
        <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-2xl font-black">Ranked Matches</h2>

            <p className="mt-1 text-sm text-slate-400">
              Review score breakdowns, save applications, and give feedback to
              improve future recommendations.
            </p>
          </div>

          <p className="text-sm text-slate-400">
            {matches.length} matches · {feedbackCount} feedback saved
          </p>
        </div>

        {isMatching && (
          <div className="mb-5 grid gap-4">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="h-52 animate-pulse rounded-[2rem] border border-slate-800 bg-slate-900/70"
              />
            ))}
          </div>
        )}

        {!isMatching && matches.length === 0 && (
          <div className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-10 text-center shadow-xl shadow-black/20 backdrop-blur">
            <p className="text-2xl font-black">No matches generated yet</p>

            <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">
              Fetch jobs from the Jobs page, confirm your active resume ID, then
              click Run Matching to generate ranked job recommendations.
            </p>

            <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                href="/jobs"
                className="rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-black text-slate-950 hover:bg-cyan-300"
              >
                Search Jobs
              </Link>

              <Link
                href="/upload-resume"
                className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm font-black hover:bg-slate-800"
              >
                Upload Resume
              </Link>
            </div>
          </div>
        )}

        <div className="grid gap-4">
          {matches.map((match, index) => {
            const jobId = getJobId(match);
            const recommendedScore = getRecommendedScore(match);
            const atsScore = getAtsScore(match);
            const mlPreferenceScore = normalizeScore(match.ml_preference_score);
            const semanticScore = normalizeScore(match.semantic_score);
            const skillScore = normalizeScore(match.skill_score);
            const matchedSkills = match.matched_skills || [];
            const missingSkills = match.missing_skills || [];
            const description = cleanDescription(match.description);
            const isExpanded = expandedJobId === jobId;
            const feedbackLabel = feedbackState[jobId];

            return (
              <article
                key={`${jobId}-${index}`}
                className="group rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/10 backdrop-blur transition hover:border-cyan-500/40"
              >
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
                  <div className="min-w-0">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-black text-slate-300">
                        Rank #{index + 1}
                      </span>

                      <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-cyan-300">
                        {getSourceLabel(match.source)}
                      </span>

                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-black ${getRecommendationClass(
                          recommendedScore
                        )}`}
                      >
                        {getRecommendationLabel(recommendedScore)}
                      </span>

                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
                        Job ID: {jobId}
                      </span>
                    </div>

                    <h3 className="text-2xl font-black leading-snug text-white group-hover:text-cyan-100">
                      {match.title || "Untitled Job"}
                    </h3>

                    <p className="mt-2 text-sm font-semibold text-slate-300">
                      {match.company || "Unknown Company"} ·{" "}
                      {match.location || "Unknown Location"}
                    </p>

                    <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                        Match Insight
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        {getMatchInsight(match)}
                      </p>
                    </div>

                    {description && (
                      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <div className="mb-2 flex items-center justify-between gap-4">
                          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                            Job Summary
                          </p>

                          <button
                            type="button"
                            onClick={() =>
                              setExpandedJobId(isExpanded ? null : jobId)
                            }
                            className="text-xs font-bold text-cyan-300 hover:text-cyan-200"
                          >
                            {isExpanded ? "Show less" : "Show more"}
                          </button>
                        </div>

                        <p
                          className={`text-sm leading-6 text-slate-400 ${
                            isExpanded ? "" : "max-h-20 overflow-hidden"
                          }`}
                        >
                          {description}
                        </p>
                      </div>
                    )}

                    <div className="mt-5 grid gap-4 lg:grid-cols-2">
                      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                        <p className="mb-3 text-xs font-black uppercase tracking-wide text-emerald-300">
                          Matched Skills
                        </p>

                        <div className="flex flex-wrap gap-2">
                          {matchedSkills.length > 0 ? (
                            matchedSkills.slice(0, 12).map((skill) => (
                              <span
                                key={`${jobId}-matched-${skill}`}
                                className="rounded-full bg-emerald-950/60 px-3 py-1 text-xs font-medium text-emerald-300 ring-1 ring-emerald-500/30"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">
                              No matched skills
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4">
                        <p className="mb-3 text-xs font-black uppercase tracking-wide text-rose-300">
                          Missing Skills
                        </p>

                        <div className="flex flex-wrap gap-2">
                          {missingSkills.length > 0 ? (
                            missingSkills.slice(0, 12).map((skill) => (
                              <span
                                key={`${jobId}-missing-${skill}`}
                                className="rounded-full bg-rose-950/60 px-3 py-1 text-xs font-medium text-rose-300 ring-1 ring-rose-500/30"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-slate-500">
                              No missing skills
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                            Feedback for future ML ranking
                          </p>

                          <p className="mt-1 text-sm text-slate-400">
                            Your feedback improves future personalized
                            recommendations.
                          </p>
                        </div>

                        {feedbackLabel && (
                          <span className="rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1 text-xs font-bold text-purple-300">
                            Saved: {feedbackLabel}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-3">
                        <button
                          type="button"
                          onClick={() => handleFeedback(jobId, "interested")}
                          className="rounded-xl border border-emerald-800 bg-emerald-950/40 px-4 py-2 text-sm font-bold text-emerald-300 hover:bg-emerald-900"
                        >
                          Interested
                        </button>

                        <button
                          type="button"
                          onClick={() => handleFeedback(jobId, "not_interested")}
                          className="rounded-xl border border-rose-800 bg-rose-950/40 px-4 py-2 text-sm font-bold text-rose-300 hover:bg-rose-900"
                        >
                          Not Interested
                        </button>

                        <button
                          type="button"
                          onClick={() => handleFeedback(jobId, "applied")}
                          className="rounded-xl border border-cyan-800 bg-cyan-950/40 px-4 py-2 text-sm font-bold text-cyan-300 hover:bg-cyan-900"
                        >
                          Applied
                        </button>
                      </div>
                    </div>
                  </div>

                  <aside className="flex flex-col gap-3">
                    <div className="rounded-[2rem] border border-cyan-500/30 bg-slate-950 p-5 shadow-lg shadow-cyan-950/20">
                      <p className="text-center text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
                        Recommended Score
                      </p>

                      <p className="mt-2 text-center text-6xl font-black text-cyan-300">
                        {formatScore(recommendedScore)}
                      </p>

                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full ${getScoreBarClass(
                            recommendedScore
                          )}`}
                          style={{
                            width: `${Math.min(
                              Math.max(recommendedScore || 0, 0),
                              100
                            )}%`,
                          }}
                        />
                      </div>

                      <div className="mt-5 grid grid-cols-2 gap-3">
                        <div className="rounded-2xl bg-slate-900 p-3 text-center">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                            ATS Match
                          </p>

                          <p className="mt-1 text-lg font-black text-white">
                            {formatScore(atsScore)}
                          </p>
                        </div>

                        <div className="rounded-2xl bg-slate-900 p-3 text-center">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                            Learned
                          </p>

                          <p className="mt-1 text-lg font-black text-white">
                            {formatScore(mlPreferenceScore)}
                          </p>
                        </div>
                      </div>

                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="rounded-2xl bg-slate-900 p-3 text-center">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                            Semantic
                          </p>

                          <p className="mt-1 text-base font-black text-white">
                            {formatScore(semanticScore)}
                          </p>
                        </div>

                        <div className="rounded-2xl bg-slate-900 p-3 text-center">
                          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                            Skills
                          </p>

                          <p className="mt-1 text-base font-black text-white">
                            {formatScore(skillScore)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {match.apply_url && (
                        <a
                          href={getSafeApplyUrl(match.apply_url)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-2xl border border-slate-700 px-4 py-3 text-center text-sm font-black hover:bg-slate-800"
                        >
                          Open Job
                        </a>
                      )}

                      <button
                        type="button"
                        onClick={() => handleSaveApplication(jobId)}
                        className="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-black text-slate-950 hover:bg-cyan-300"
                      >
                        Save
                      </button>
                    </div>
                  </aside>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </AppShell>
  );
}