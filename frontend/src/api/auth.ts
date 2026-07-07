export function getAccessToken(): string | null {
  return localStorage.getItem("sentinel_access_token");
}

export function setAccessToken(token: string): void {
  localStorage.setItem("sentinel_access_token", token);
}

export function clearAccessToken(): void {
  localStorage.removeItem("sentinel_access_token");
}
