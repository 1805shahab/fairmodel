/** Display the backend's decimal text verbatim. No currency arithmetic or rounding. */
export function money(amount: string | number, currency = "USD"): string {
  const value = String(amount);
  const symbols: Readonly<Record<string, string>> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
  };
  return symbols[currency]
    ? `${symbols[currency]}${value}`
    : `${currency} ${value}`;
}
