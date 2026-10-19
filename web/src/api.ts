export class ApiError extends Error {
  readonly kind: 'network' | 'http' | 'invalid_response';
  readonly status?: number;
  readonly details?: string;

  constructor(
    message: string,
    kind: ApiError['kind'],
    options: { status?: number; details?: string } = {},
  ) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = options.status;
    this.details = options.details;
  }
}

async function readResponseBody(response: Response): Promise<unknown> {
  const raw = await response.text();
  const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';

  if (!raw.trim()) {
    throw new ApiError(
      `Backend returned an empty response (HTTP ${response.status}).`,
      'invalid_response',
      { status: response.status },
    );
  }
  if (!contentType.includes('application/json')) {
    throw new ApiError(
      `Backend returned ${contentType || 'an unknown content type'} instead of JSON.`,
      'invalid_response',
      { status: response.status, details: raw.slice(0, 500) },
    );
  }
  try {
    return JSON.parse(raw);
  } catch {
    throw new ApiError(
      `Backend returned malformed JSON (HTTP ${response.status}).`,
      'invalid_response',
      { status: response.status, details: raw.slice(0, 500) },
    );
  }
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network request failed.';
    throw new ApiError(`Unable to reach the InvariantQ backend: ${message}`, 'network');
  }

  const data = await readResponseBody(response);
  if (!response.ok) {
    const message =
      typeof data === 'object' && data !== null && 'message' in data
        ? String((data as { message: unknown }).message)
        : `Backend request failed with HTTP ${response.status}.`;
    throw new ApiError(message, 'http', { status: response.status });
  }
  return data as T;
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
