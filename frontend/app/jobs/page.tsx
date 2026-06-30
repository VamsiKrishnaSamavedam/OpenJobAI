"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import {
  fetchMultiSourceJobs,
  getJobs,
  saveApplication,
  searchAndFetchJobs,
} from "@/lib/api";

type AtsDetails = {
  score?: number;
  final_score?: number;
  ats_score?: number;
  ats_compatibility_score?: number;
  semantic_score?: number;
  skill_score?: number;
  ml_preference_score?: number | null;
  recommended_score?: number;
  required_skill_score?: number;
  preferred_skill_score?: number;
  experience_score?: number;
  title_score?: number;
  education_score?: number;
  keyword_context_score?: number;
  location_score?: number;
  matched_skills?: string[];
  missing_skills?: string[];
  knockout_flags?: string[];
  ats_explanation?: string[];
};

type Job = {
  id: number;
  source: string | null;
  source_job_id: string | null;
  title: string | null;
  company: string | null;
  location: string | null;
  description: string | null;
  apply_url: string | null;
  extracted_skills: string[] | null;
  created_at: string;
  ats_score?: number;
  ats_compatibility_score?: number;
  ml_preference_score?: number | null;
  recommended_score?: number;
  ats_details?: AtsDetails;
};

const PAGE_SIZE = 20;
const SELECTED_RESUME_STORAGE_KEY = "openjobai_selected_resume_id";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [offset, setOffset] = useState<number>(0);
  const [hasMoreJobs, setHasMoreJobs] = useState<boolean>(true);

  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [freshnessFilter, setFreshnessFilter] = useState<string>("all");
  const [relevantOnly, setRelevantOnly] = useState<boolean>(false);

  const [resumeId, setResumeId] = useState<string>("");
  const [searchText, setSearchText] = useState<string>("");
  const [locationText, setLocationText] = useState<string>("United States");
  const [activeSearch, setActiveSearch] = useState<string>("");
  const [liveFetchLimit, setLiveFetchLimit] = useState<number>(20);

  const [isFetching, setIsFetching] = useState<boolean>(false);
  const [isSearchingLive, setIsSearchingLive] = useState<boolean>(false);
  const [isLoadingJobs, setIsLoadingJobs] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);

  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  function normalizeScore(value: number | null | undefined) {
    if (value === null || value === undefined) {
      return undefined;
    }

    const numericValue = Number(value);

    if (Number.isNaN(numericValue)) {
      return undefined;
    }

    if (numericValue <= 1) {
      return Math.round(numericValue * 100);
    }

    return Math.round(numericValue);
  }

  function formatScore(value: number | null | undefined) {
    const score = normalizeScore(value);

    if (score === undefined) {
      return "N/A";
    }

    return `${score}%`;
  }

  function getRecommendedScore(job: Job) {
    return (
      normalizeScore(job.recommended_score) ??
      normalizeScore(job.ats_details?.recommended_score) ??
      normalizeScore(job.ats_score) ??
      normalizeScore(job.ats_details?.final_score)
    );
  }

  function getAtsScore(job: Job) {
    return (
      normalizeScore(job.ats_compatibility_score) ??
      normalizeScore(job.ats_score) ??
      normalizeScore(job.ats_details?.ats_compatibility_score) ??
      normalizeScore(job.ats_details?.final_score)
    );
  }

  function getSourceLabel(source: string | null) {
    const value = (source || "").toLowerCase();

    if (value.includes("linkedin")) {
      return "LinkedIn";
    }

    if (value.includes("indeed")) {
      return "Indeed";
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

    return applyUrl;
  }

  function cleanJobDescription(description: string | null) {
    if (!description) {
      return "No description available.";
    }

    return description
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&nbsp;/g, " ")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&rsquo;/g, "'")
      .replace(/&lsquo;/g, "'")
      .replace(/&ldquo;/g, '"')
      .replace(/&rdquo;/g, '"')
      .replace(/\s+/g, " ")
      .trim();
  }

  function getRecommendationLabel(score: number | undefined) {
    if (score === undefined) {
      return "Not scored";
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

  async function loadSavedJobs(
    searchValue: string = activeSearch,
    selectedResumeId: string = resumeId
  ) {
    try {
      setIsLoadingJobs(true);
      setError("");
      setMessage("");

      const data = await getJobs(
        PAGE_SIZE,
        0,
        searchValue,
        sourceFilter,
        freshnessFilter,
        relevantOnly,
        selectedResumeId
      );

      setJobs(data);
      setOffset(data.length);
      setHasMoreJobs(data.length === PAGE_SIZE);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load saved jobs.");
      }
    } finally {
      setIsLoadingJobs(false);
    }
  }

  async function runLiveJobSearch(
    query: string,
    location: string,
    limit: number,
    selectedResumeId: string
  ) {
    const cleanedQuery = query.trim();

    if (!cleanedQuery) {
      setError("Enter a job title or keyword before searching.");
      return;
    }

    try {
      setIsSearchingLive(true);
      setError("");
      setMessage("");
      setJobs([]);
      setActiveSearch(cleanedQuery);

      const data = await searchAndFetchJobs(
        cleanedQuery,
        location.trim() || "United States",
        limit,
        selectedResumeId
      );

      const returnedJobs = Array.isArray(data) ? data : data.jobs || [];

      setJobs(returnedJobs);
      setOffset(returnedJobs.length);
      setHasMoreJobs(returnedJobs.length === PAGE_SIZE);

      setMessage(
        data.message ||
          `Fetched and scored ${returnedJobs.length} jobs for "${cleanedQuery}".`
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Live job search failed.");
      }
    } finally {
      setIsSearchingLive(false);
    }
  }

  async function loadMoreJobs() {
    try {
      setIsLoadingMore(true);
      setError("");
      setMessage("");

      const data = await getJobs(
        PAGE_SIZE,
        offset,
        activeSearch,
        sourceFilter,
        freshnessFilter,
        relevantOnly,
        resumeId
      );

      setJobs((currentJobs) => [...currentJobs, ...data]);
      setOffset((currentOffset) => currentOffset + data.length);
      setHasMoreJobs(data.length === PAGE_SIZE);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load more jobs.");
      }
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleFetchJobs() {
    try {
      setIsFetching(true);
      setError("");
      setMessage("");

      const data = await fetchMultiSourceJobs();

      setMessage(
        `Fetched latest default jobs successfully. Saved or updated ${data.fetched_count} jobs.`
      );

      await loadSavedJobs(activeSearch, resumeId);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to fetch default jobs.");
      }
    } finally {
      setIsFetching(false);
    }
  }

  async function handleSaveApplication(jobId: number) {
    try {
      setError("");
      setMessage("");

      const data = await saveApplication(
        jobId,
        "saved",
        "Saved from OpenJobAI jobs page."
      );

      setMessage(
        `Job ID ${jobId} saved to application tracker. Application ID: ${data.application_id}`
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(`Save failed: ${err.message}`);
      } else {
        setError("Save failed: unknown error.");
      }
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    await runLiveJobSearch(searchText, locationText, liveFetchLimit, resumeId);
  }

  async function clearSearch() {
    setSearchText("");
    setActiveSearch("");

    await loadSavedJobs("", resumeId);
  }

  async function applyQuickFilter(filterValue: string) {
    setSearchText(filterValue);
    setActiveSearch(filterValue);

    await runLiveJobSearch(filterValue, locationText, liveFetchLimit, resumeId);
  }

  async function handleApplyFilters() {
    await loadSavedJobs(activeSearch, resumeId);
  }

  useEffect(() => {
    const storedResumeId = localStorage.getItem(SELECTED_RESUME_STORAGE_KEY);

    if (storedResumeId) {
      setResumeId(storedResumeId);
      loadSavedJobs("", storedResumeId);
    } else {
      loadSavedJobs("");
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const topScore =
    jobs.length > 0 ? Math.max(...jobs.map((job) => getRecommendedScore(job) || 0)) : 0;

  const scoredJobsCount = jobs.filter(
    (job) => getRecommendedScore(job) !== undefined
  ).length;

  return (
    <AppShell
      badge="Live Job Search"
      title="Search fresh jobs and rank them by resume fit."
      subtitle="Fetch new jobs from LinkedIn and Indeed, save them to PostgreSQL, and score each opportunity using ATS compatibility plus your learned XGBoost preference model."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/upload-resume"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            Upload Resume
          </Link>

          <Link
            href="/matches"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
          >
            View Matches
          </Link>
        </div>
      }
    >
      <section className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Loaded Jobs
          </p>
          <p className="mt-2 text-3xl font-black">{jobs.length}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Scored Jobs
          </p>
          <p className="mt-2 text-3xl font-black">{scoredJobsCount}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Top Score
          </p>
          <p className="mt-2 text-3xl font-black text-cyan-300">
            {topScore ? `${topScore}%` : "N/A"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/85 p-4 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-xs font-black uppercase tracking-wide text-slate-500">
            Active Resume
          </p>
          <p className="mt-2 truncate text-3xl font-black text-purple-300">
            {resumeId ? `ID ${resumeId}` : "None"}
          </p>
        </div>
      </section>

      <section className="mb-6 rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/20 backdrop-blur">
        <form
          onSubmit={handleSearch}
          className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(220px,0.7fr)_150px_170px]"
        >
          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Search Fresh Jobs
            </label>

            <input
              type="text"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Example: Data Engineer, Python Developer, ETL Analyst..."
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Location
            </label>

            <input
              type="text"
              value={locationText}
              onChange={(event) => setLocationText(event.target.value)}
              placeholder="United States"
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Limit
            </label>

            <select
              value={liveFetchLimit}
              onChange={(event) => setLiveFetchLimit(Number(event.target.value))}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value={10}>10 jobs</option>
              <option value={20}>20 jobs</option>
              <option value={30}>30 jobs</option>
              <option value={50}>50 jobs</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isSearchingLive}
            className="rounded-2xl bg-cyan-400 px-6 py-3 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60 xl:self-end"
          >
            {isSearchingLive ? "Searching..." : "Search New Jobs"}
          </button>
        </form>

        <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto_auto]">
          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Source Filter
            </label>

            <select
              value={sourceFilter}
              onChange={(event) => setSourceFilter(event.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value="all">Indeed + LinkedIn</option>
              <option value="indeed">Indeed only</option>
              <option value="linkedin">LinkedIn only</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Freshness
            </label>

            <select
              value={freshnessFilter}
              onChange={(event) => setFreshnessFilter(event.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
            >
              <option value="all">All saved jobs</option>
              <option value="24h">Fetched in last 24 hours</option>
              <option value="7d">Fetched in last 7 days</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs font-black uppercase tracking-wide text-slate-500">
              Relevance
            </label>

            <button
              type="button"
              onClick={() => setRelevantOnly((currentValue) => !currentValue)}
              className={`w-full rounded-2xl px-4 py-3 text-sm font-black ${
                relevantOnly
                  ? "bg-cyan-400 text-slate-950"
                  : "bg-slate-800 text-white hover:bg-slate-700"
              }`}
            >
              {relevantOnly ? "Relevant Only: ON" : "Relevant Only: OFF"}
            </button>
          </div>

          <button
            type="button"
            onClick={handleApplyFilters}
            disabled={isLoadingJobs}
            className="rounded-2xl bg-slate-800 px-6 py-3 text-sm font-black hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
          >
            {isLoadingJobs ? "Loading..." : "Refresh Saved"}
          </button>

          <button
            type="button"
            onClick={handleFetchJobs}
            disabled={isFetching}
            className="rounded-2xl border border-slate-700 bg-slate-900 px-6 py-3 text-sm font-black hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
          >
            {isFetching ? "Fetching..." : "Fetch Default"}
          </button>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {[
            "Data Engineer",
            "Data Analyst",
            "Software Engineer",
            "Python Developer",
            "SQL Developer",
            "Machine Learning Engineer",
            "ETL Developer",
            "Cloud Engineer",
          ].map((filterValue) => (
            <button
              key={filterValue}
              type="button"
              onClick={() => applyQuickFilter(filterValue)}
              disabled={isSearchingLive}
              className="rounded-full border border-slate-700 bg-slate-950 px-4 py-2 text-xs font-bold text-slate-300 hover:border-cyan-500 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {filterValue}
            </button>
          ))}
        </div>

        {!resumeId && (
          <div className="mt-5 rounded-2xl border border-amber-800 bg-amber-950/30 p-4 text-sm text-amber-300">
            No active resume selected. Go to the Upload Resume page and choose a
            resume to calculate ATS Compatibility and Learned Preference scores.
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
            <h2 className="text-2xl font-black">Ranked Jobs</h2>

            <p className="mt-1 text-sm text-slate-400">
              Live results are saved, scored, and ranked by Recommended Score
              when a resume is selected.
            </p>
          </div>

          <button
            type="button"
            onClick={() => loadSavedJobs(activeSearch, resumeId)}
            disabled={isLoadingJobs}
            className="rounded-2xl bg-slate-800 px-5 py-3 text-sm font-black hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoadingJobs ? "Refreshing..." : "Reload Saved Jobs"}
          </button>
        </div>

        {(isSearchingLive || isLoadingJobs) && (
          <div className="mb-5 grid gap-4">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="h-44 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/70"
              />
            ))}
          </div>
        )}

        {!isSearchingLive && !isLoadingJobs && jobs.length === 0 && (
          <div className="rounded-3xl border border-slate-800 bg-slate-950/85 p-10 text-center shadow-xl shadow-black/20 backdrop-blur">
            <p className="text-2xl font-black">No jobs loaded yet</p>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-400">
              Search fresh jobs using a role like Data Engineer or Python
              Developer. The app will fetch from LinkedIn and Indeed, save the
              jobs, and score them against your selected resume.
            </p>
          </div>
        )}

        <div className="grid gap-4">
          {jobs.map((job) => {
            const cleanedDescription = cleanJobDescription(job.description);
            const uniqueSkills = Array.from(new Set(job.extracted_skills || []));

            const recommendedScore = getRecommendedScore(job);
            const atsScore = getAtsScore(job);

            const mlPreferenceScore =
              normalizeScore(job.ml_preference_score) ??
              normalizeScore(job.ats_details?.ml_preference_score);

            const semanticScore = normalizeScore(job.ats_details?.semantic_score);
            const skillScore = normalizeScore(job.ats_details?.skill_score);

            const sourceLabel = getSourceLabel(job.source);

            return (
              <article
                key={job.id}
                className="group rounded-[2rem] border border-slate-800 bg-slate-950/85 p-5 shadow-xl shadow-black/10 backdrop-blur transition hover:border-cyan-500/40"
              >
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
                  <div className="min-w-0">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-cyan-300">
                        {sourceLabel}
                      </span>

                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
                        Job ID: {job.id}
                      </span>

                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-black ${getRecommendationClass(
                          recommendedScore
                        )}`}
                      >
                        {getRecommendationLabel(recommendedScore)}
                      </span>
                    </div>

                    <h3 className="text-2xl font-black leading-snug text-white group-hover:text-cyan-100">
                      {job.title || "Untitled Job"}
                    </h3>

                    <p className="mt-2 text-sm font-semibold text-slate-300">
                      {job.company || "Unknown Company"} ·{" "}
                      {job.location || "Unknown Location"}
                    </p>

                    <p className="mt-4 max-h-24 overflow-hidden text-sm leading-6 text-slate-400">
                      {cleanedDescription}
                    </p>

                    {job.ats_details?.ats_explanation &&
                      job.ats_details.ats_explanation.length > 0 && (
                        <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                          <p className="mb-2 text-xs font-black uppercase tracking-wide text-slate-500">
                            ATS Explanation
                          </p>

                          <ul className="space-y-1 text-sm text-slate-300">
                            {job.ats_details.ats_explanation
                              .slice(0, 3)
                              .map((item, index) => (
                                <li key={`${job.id}-explanation-${index}`}>
                                  {item}
                                </li>
                              ))}
                          </ul>
                        </div>
                      )}

                    <div className="mt-5 border-t border-slate-800 pt-4">
                      <div className="mb-3 flex items-center justify-between">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                          Extracted Skills
                        </p>

                        {uniqueSkills.length > 12 && (
                          <p className="text-xs text-slate-500">
                            Showing 12 of {uniqueSkills.length}
                          </p>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {uniqueSkills.length > 0 ? (
                          uniqueSkills.slice(0, 12).map((skill, index) => (
                            <span
                              key={`${job.id}-${skill}-${index}`}
                              className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-slate-300 ring-1 ring-slate-700"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-slate-500">
                            No skills extracted
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <aside className="flex flex-col gap-3">
                    {typeof recommendedScore === "number" ? (
                      <div className="rounded-[2rem] border border-cyan-500/30 bg-slate-950 p-5 shadow-lg shadow-cyan-950/20">
                        <p className="text-center text-xs font-black uppercase tracking-[0.2em] text-cyan-300">
                          Recommended Score
                        </p>

                        <p className="mt-2 text-center text-6xl font-black text-cyan-300">
                          {formatScore(recommendedScore)}
                        </p>

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

                        {job.ats_details?.matched_skills &&
                          job.ats_details.matched_skills.length > 0 && (
                            <div className="mt-4 rounded-2xl bg-emerald-500/10 p-3">
                              <p className="text-[10px] font-black uppercase tracking-wide text-emerald-300">
                                Matched Skills
                              </p>

                              <p className="mt-1 max-h-10 overflow-hidden text-xs leading-5 text-emerald-300">
                                {job.ats_details.matched_skills
                                  .slice(0, 6)
                                  .join(", ")}
                              </p>
                            </div>
                          )}

                        {job.ats_details?.missing_skills &&
                          job.ats_details.missing_skills.length > 0 && (
                            <div className="mt-3 rounded-2xl bg-rose-500/10 p-3">
                              <p className="text-[10px] font-black uppercase tracking-wide text-rose-300">
                                Missing Skills
                              </p>

                              <p className="mt-1 max-h-10 overflow-hidden text-xs leading-5 text-rose-300">
                                {job.ats_details.missing_skills
                                  .slice(0, 6)
                                  .join(", ")}
                              </p>
                            </div>
                          )}
                      </div>
                    ) : (
                      <div className="rounded-[2rem] border border-slate-700 bg-slate-950 p-5 text-center">
                        <p className="text-xs font-black uppercase tracking-wide text-slate-400">
                          Recommended Score
                        </p>

                        <p className="mt-3 text-sm text-slate-500">
                          Select a resume to score this job.
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3">
                      {job.apply_url && (
                        <a
                          href={getSafeApplyUrl(job.apply_url)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-2xl border border-slate-700 px-4 py-3 text-center text-sm font-black hover:bg-slate-800"
                        >
                          Open Job
                        </a>
                      )}

                      <button
                        type="button"
                        onClick={() => handleSaveApplication(job.id)}
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

        {jobs.length > 0 && hasMoreJobs && (
          <div className="mt-8 flex justify-center">
            <button
              type="button"
              onClick={loadMoreJobs}
              disabled={isLoadingMore}
              className="rounded-2xl bg-slate-800 px-8 py-3 text-sm font-black hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoadingMore ? "Loading more jobs..." : "Load More Saved Jobs"}
            </button>
          </div>
        )}

        {jobs.length > 0 && !hasMoreJobs && (
          <div className="mt-8 text-center text-sm text-slate-500">
            No more saved jobs to load.
          </div>
        )}
      </section>
    </AppShell>
  );
}