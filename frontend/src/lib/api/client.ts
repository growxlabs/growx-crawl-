/**
 * GrowX AutoGTM Typed API Client.
 * Handles unified HTTP requests, error handling, query param formatting, and proxy fallbacks.
 */

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    // In browser: use relative paths which Next.js rewrites to FastAPI backend
    return "";
  }
  return process.env.FASTAPI_URL || "http://127.0.0.1:7411";
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    let errorData = null;
    try {
      errorData = await response.json();
      errorDetail = errorData.detail || errorData.message || JSON.stringify(errorData);
    } catch {
      // ignore json parse error
    }
    throw new ApiError(response.status, errorDetail, errorData);
  }

  return response.json() as Promise<T>;
}
