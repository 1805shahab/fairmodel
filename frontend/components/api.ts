export const PAYMENT_NOTICE =
  "DEMO / SIMULATED PAYMENT — NO REAL FUNDS TRANSFERRED";
export const endpoint = (path: string) => `/api/backend${path}`;
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(endpoint(path), {
    ...init,
    cache: "no-store",
    headers:
      init?.body instanceof FormData
        ? undefined
        : { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json();
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail
              .map(
                (x: { loc: string[]; msg: string }) =>
                  `${x.loc.join(".")}: ${x.msg}`,
              )
              .join("; ")
          : "Request failed. Please retry.";
    throw new Error(detail);
  }
  return data;
}
export const post = <T>(path: string, body: unknown = {}) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
export function money(amount: string | number, currency = "USD") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(
    Number(amount),
  );
}
export function date(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "Asia/Karachi",
  }).format(new Date(value));
}
export function statusLabel(status: string) {
  if (status === "PAID") return "paid (Sandbox)";
  if (status === "INVOICE_PAID") return "invoice paid (Sandbox)";
  if (status === "ANALYZED") return "audio analyzed";
  return status.toLowerCase().replaceAll("_", " ");
}
