"use client";

import { useState, type ChangeEvent } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { uploadResume } from "@/lib/api";

type ResumeUploadResult = {
  resume_id: number;
  filename: string;
  text_length: number;
  extracted_skills: string[];
  embedding_length: number;
  message: string;
};

const SELECTED_RESUME_STORAGE_KEY = "openjobai_selected_resume_id";

export default function UploadResumePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ResumeUploadResult | null>(null);
  const [error, setError] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setResult(null);
    setError("");
  }

  function handleDroppedFile(file: File | undefined) {
    if (!file) {
      return;
    }

    const allowedExtensions = [".pdf", ".docx", ".txt"];
    const fileName = file.name.toLowerCase();

    const isAllowed = allowedExtensions.some((extension) =>
      fileName.endsWith(extension)
    );

    if (!isAllowed) {
      setError("Please upload a PDF, DOCX, or TXT resume file.");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setResult(null);
    setError("");
  }

  function formatFileSize(sizeInBytes: number) {
    if (sizeInBytes < 1024 * 1024) {
      return `${(sizeInBytes / 1024).toFixed(2)} KB`;
    }

    return `${(sizeInBytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("Please select a resume file first.");
      return;
    }

    try {
      setIsUploading(true);
      setError("");
      setResult(null);

      const data = await uploadResume(selectedFile);

      setResult(data);

      localStorage.setItem("latest_resume_id", String(data.resume_id));
      localStorage.setItem(
        SELECTED_RESUME_STORAGE_KEY,
        String(data.resume_id)
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Resume upload failed.");
      }
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <AppShell
      badge="Resume Intelligence"
      title="Turn your resume into an AI-ready candidate profile."
      subtitle="Upload a PDF, DOCX, or TXT resume. OpenJobAI extracts text, detects skills, generates embeddings, and makes the resume available for ATS scoring and personalized job ranking."
      actions={
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/jobs"
            className="rounded-2xl bg-cyan-400 px-5 py-3 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
          >
            Search Jobs
          </Link>

          <Link
            href="/matches"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-3 text-center text-sm font-black hover:bg-slate-800"
          >
            View Matches
          </Link>
        </div>
      }
    >
      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-cyan-300">
            Upload File
          </p>

          <h2 className="mt-3 text-3xl font-black">Resume source</h2>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Choose your latest resume. For best results, use a resume with clear
            project descriptions, technical skills, education, and experience
            sections.
          </p>

          <div
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              handleDroppedFile(event.dataTransfer.files?.[0]);
            }}
            className={`mt-6 rounded-[2rem] border border-dashed p-8 text-center transition ${
              isDragging
                ? "border-cyan-400 bg-cyan-500/10"
                : "border-slate-700 bg-slate-900/70"
            }`}
          >
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-cyan-400 text-2xl font-black text-slate-950">
              ↑
            </div>

            <p className="mt-4 text-lg font-black">
              Drag and drop your resume
            </p>

            <p className="mt-2 text-sm text-slate-400">
              Supports PDF, DOCX, and TXT files.
            </p>

            <label className="mt-6 inline-flex cursor-pointer rounded-2xl bg-cyan-400 px-6 py-3 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300">
              Browse File
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {selectedFile && (
            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Selected File
                  </p>

                  <p className="mt-2 font-black text-white">
                    {selectedFile.name}
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    Size: {formatFileSize(selectedFile.size)}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setResult(null);
                    setError("");
                  }}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-bold text-slate-300 hover:bg-slate-800"
                >
                  Remove
                </button>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleUpload}
            disabled={isUploading || !selectedFile}
            className="mt-6 w-full rounded-2xl bg-cyan-400 px-6 py-4 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? "Uploading and processing..." : "Upload Resume"}
          </button>

          {error && (
            <div className="mt-6 rounded-2xl border border-rose-800 bg-rose-950 p-4 text-sm text-rose-300">
              {error}
            </div>
          )}
        </section>

        <section className="rounded-[2rem] border border-slate-800 bg-slate-950/85 p-6 shadow-xl shadow-black/20 backdrop-blur">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-purple-300">
            Processing Result
          </p>

          {!result && !isUploading && (
            <div className="mt-6 rounded-[2rem] border border-slate-800 bg-slate-900/70 p-8 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-800 text-2xl font-black text-slate-500">
                AI
              </div>

              <p className="mt-4 text-xl font-black">
                Resume analysis will appear here
              </p>

              <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">
                After upload, you will see the resume ID, extracted text length,
                embedding length, and detected skills.
              </p>
            </div>
          )}

          {isUploading && (
            <div className="mt-6 space-y-4">
              <div className="h-28 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/70" />
              <div className="h-28 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/70" />
              <div className="h-40 animate-pulse rounded-3xl border border-slate-800 bg-slate-900/70" />
            </div>
          )}

          {result && (
            <div className="mt-6">
              <div className="rounded-[2rem] border border-emerald-800 bg-emerald-950/40 p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-sm font-black uppercase tracking-wide text-emerald-300">
                      Resume uploaded successfully
                    </p>

                    <h2 className="mt-2 text-3xl font-black text-white">
                      Resume ID {result.resume_id}
                    </h2>

                    <p className="mt-2 text-sm text-emerald-200">
                      This resume is now selected as your active resume.
                    </p>
                  </div>

                  <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-xs font-black uppercase tracking-wide text-emerald-300">
                    Active
                  </span>
                </div>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Filename
                  </p>

                  <p className="mt-2 truncate font-black">{result.filename}</p>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Resume ID
                  </p>

                  <p className="mt-2 text-2xl font-black text-cyan-300">
                    {result.resume_id}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Extracted Text Length
                  </p>

                  <p className="mt-2 text-2xl font-black">
                    {result.text_length.toLocaleString()}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                    Embedding Length
                  </p>

                  <p className="mt-2 text-2xl font-black">
                    {result.embedding_length.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="mt-6 rounded-[2rem] border border-slate-800 bg-slate-900/70 p-5">
                <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                      Extracted Skills
                    </p>

                    <p className="mt-1 text-sm text-slate-400">
                      These skills will be used for ATS compatibility and job
                      matching.
                    </p>
                  </div>

                  <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-bold text-cyan-300">
                    {result.extracted_skills.length} skills
                  </span>
                </div>

                <div className="flex max-h-52 flex-wrap gap-2 overflow-y-auto pr-1">
                  {result.extracted_skills.length > 0 ? (
                    result.extracted_skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-300 ring-1 ring-cyan-500/30"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">
                      No skills extracted.
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-2">
                <Link
                  href="/jobs"
                  className="rounded-2xl bg-cyan-400 px-5 py-4 text-center text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20 hover:bg-cyan-300"
                >
                  Continue to Job Search
                </Link>

                <Link
                  href="/matches"
                  className="rounded-2xl border border-slate-700 bg-slate-900 px-5 py-4 text-center text-sm font-black hover:bg-slate-800"
                >
                  View Matches
                </Link>
              </div>
            </div>
          )}
        </section>
      </section>
    </AppShell>
  );
}