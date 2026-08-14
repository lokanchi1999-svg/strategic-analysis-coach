/** One project-wide source for the backend URL used by browser API calls. */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export function backendNetworkErrorMessage(): string {
  return `无法连接后端：${API_BASE_URL}\n请确认 FastAPI 已启动以及 API URL / CORS 配置正确。`;
}
