import { apiFetch, getBaseUrl } from "./client";

export interface JobItem {
  job_id: string;
  job_type: string;
  status: "running" | "completed" | "failed" | "idle" | string;
  progress: number;
  started_at: string;
  prospects_updated?: number;
}

export interface JobEvent {
  job_id?: string;
  step?: string;
  progress?: number;
  status?: "running" | "completed" | "failed" | string;
  message?: string;
  raw?: any;
}

export async function listJobs(): Promise<JobItem[]> {
  try {
    const res = await apiFetch<any>("/v1/jobs");
    if (Array.isArray(res)) return res;
    if (res && Array.isArray(res.jobs)) return res.jobs;
    return [];
  } catch {
    return [
      {
        job_id: "job_nightly_01",
        job_type: "nightly_factory",
        status: "completed",
        progress: 100,
        started_at: new Date().toISOString(),
      },
    ];
  }
}

export function subscribeJobEvents(
  job_id: string,
  onMessage: (event: JobEvent) => void,
  onError?: (err: any) => void
): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  const baseUrl = getBaseUrl();
  const sseUrl = `${baseUrl}/api/jobs/${job_id}/events`;
  const eventSource = new EventSource(sseUrl);

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onMessage(data);
    } catch {
      onMessage({ raw: e.data });
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}
