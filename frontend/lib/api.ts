const API_BASE_URL = "http://127.0.0.1:8000";

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Failed to check backend health");
  }

  return response.json();
}

export async function fetchJobs(limit: number = 10) {
  const response = await fetch(`${API_BASE_URL}/jobs/fetch?limit=${limit}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch jobs");
  }

  return response.json();
}

export async function getJobs(
  limit: number = 20,
  offset: number = 0,
  search: string = "",
  sourceFilter: string = "all",
  freshness: string = "all",
  relevantOnly: boolean = false,
  resumeId: string=""
) {
  const params = new URLSearchParams();

  params.set("limit", String(limit));
  params.set("offset", String(offset));
  params.set("source_filter", sourceFilter);
  params.set("freshness", freshness);
  params.set("relevant_only", String(relevantOnly));

  if (search.trim()) {
    params.set("search", search.trim());
  }

  if(resumeId.trim()) {
    params.set("resume_id",resumeId.trim());
  }

  const response = await fetch(`${API_BASE_URL}/jobs?${params.toString()}`);

  if (!response.ok) {
    throw new Error("Failed to get jobs");
  }

  return response.json();
}

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/resumes/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to upload resume");
  }

  return response.json();
}

export async function matchResume(resumeId: number, limit: number = 10) {
  const response = await fetch(
    `${API_BASE_URL}/match/resume/${resumeId}?limit=${limit}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to match resume");
  }

  return response.json();
}

export async function saveApplication(
  jobId: number,
  status: string = "saved",
  notes: string = ""
) {
  const response = await fetch(`${API_BASE_URL}/applications/save`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_id: jobId,
      status,
      notes,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    console.error("Save application error:", errorData);
    throw new Error(errorData.detail || "Failed to save application");
  }

  return response.json();
}

export async function getApplications(limit: number = 50) {
  const response = await fetch(`${API_BASE_URL}/applications?limit=${limit}`);

  if (!response.ok) {
    throw new Error("Failed to get applications");
  }

  return response.json();
}

export async function saveFeedback(
  resumeId: number,
  jobId: number,
  feedbackLabel: string
) {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      resume_id: resumeId,
      job_id: jobId,
      feedback_label: feedbackLabel,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to save feedback");
  }

  return response.json();
}

export async function updateApplicationStatus(
  applicationId: number,
  status: string,
  notes: string = ""
) {
  const response = await fetch(
    `${API_BASE_URL}/applications/${applicationId}/status`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status,
        notes,
      }),
    }
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to update application status");
  }

  return response.json();
}

export async function deleteApplication(applicationId: number) {
  const response = await fetch(
    `${API_BASE_URL}/applications/${applicationId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to delete application");
  }

  return response.json();
}

export async function fetchMultiSourceJobs() {
  const response = await fetch(`${API_BASE_URL}/jobs/fetch/multi-source`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to fetch multi-source jobs");
  }

  return response.json();
}

export async function getResumes() {
  const response = await fetch(`${API_BASE_URL}/resumes`);

  if (!response.ok) {
    throw new Error("Failed to get resumes");
  }

  return response.json();
}

export async function searchAndFetchJobs(
  query: string,
  location: string = "",
  limit: number = 20,
  resumeId: string = ""
) {
  const params = new URLSearchParams();

  params.set("query", query.trim());
  params.set("limit", String(limit));

  if (location.trim()) {
    params.set("location", location.trim());
  }

  if (resumeId.trim()) {
    params.set("resume_id", resumeId.trim());
  }

  const response = await fetch(
    `${API_BASE_URL}/jobs/search-fetch?${params.toString()}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to search and fetch jobs");
  }

  return response.json();
}

export async function getDashboardStats() {
  const response = await fetch(`${API_BASE_URL}/dashboard/stats`);

  if (!response.ok) {
    throw new Error("Failed to load dashboard stats");
  }

  return response.json();
}

export async function deleteResume(resumeId: number) {
  const response = await fetch(`${API_BASE_URL}/resumes/${resumeId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to delete resume");
  }

  return response.json();
}