let token: string | null = null;
let refreshing: Promise<boolean> | null = null;
export function setToken(value: string | null) { token = value; }
async function refreshAccess() {
  const response = await fetch('/api/v1/auth/refresh', {method: 'POST', credentials: 'include', headers: {'X-MathMate-Client': 'web'}});
  if (!response.ok) {token = null; return false;}
  token = (await response.json()).access_token;
  return true;
}
async function coordinatedRefresh(): Promise<boolean> {
  // Await flattens the Web Locks callback's promise across TypeScript DOM versions.
  if (typeof navigator !== 'undefined' && navigator.locks) {
    return await navigator.locks.request('mathmate-refresh', refreshAccess);
  }
  return refreshAccess();
}
export async function restore() {
  // Coordinate cookie rotation across tabs as well as concurrent requests in this tab.
  if (!refreshing) refreshing = coordinatedRefresh().catch(() => false).finally(() => {refreshing = null;});
  return refreshing;
}
export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('X-MathMate-Client', 'web');
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch('/api/v1' + path, {...options, headers, credentials: 'include'});
  if (response.status === 401 && retry && !path.startsWith('/auth/') && await restore()) return api<T>(path, options, false);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your input and try again.');
  }
  return response.json();
}
export const post = <T,>(path: string, body: unknown = {}) => api<T>(path, {method: 'POST', body: JSON.stringify(body)});
