import { endpoint } from "./api";
import type { Evidence } from "./types";

export function visibleCitations(
  items: Evidence[] = [],
  requireVerified = false,
): Evidence[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (
      typeof item.quote !== "string" ||
      !item.quote.trim() ||
      !Number.isInteger(item.page) ||
      item.page < 1 ||
      !item.field?.trim() ||
      (requireVerified && item.verified !== true)
    )
      return false;
    const key = `${item.field}:${item.page}:${item.quote.trim().replace(/\s+/g, " ")}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export default function SourceCitations({
  items,
  licenseId,
  requireVerified = true,
  onSelect,
}: {
  items: Evidence[];
  licenseId: string;
  requireVerified?: boolean;
  onSelect?: (item: Evidence) => void;
}) {
  const citations = visibleCitations(items, requireVerified);
  return (
    <div className="evidence-list">
      {citations.length ? (
        citations.map((item, index) => (
          <article key={index}>
            <span className="eyebrow">
              {item.field.replaceAll("_", " ")} · PAGE {item.page}
            </span>
            <blockquote>{item.quote}</blockquote>
            {onSelect && (
              <button
                className="button secondary small-button"
                onClick={() => onSelect(item)}
              >
                Highlight source passage
              </button>
            )}
            {item.origin === "source_text_match" && (
              <p className="small">
                Recovered by exact source-text matching; approved terms
                unchanged.
              </p>
            )}
            <a
              className="text-link"
              href={`${endpoint(`/licenses/${licenseId}/contract`)}#page=${item.page}`}
              target="_blank"
              rel="noreferrer"
            >
              Open source page {item.page} ↗
            </a>
          </article>
        ))
      ) : (
        <p className="muted">
          No verified source quotations available. Review the PDF and
          reevaluate; no quotations or page references have been invented.
        </p>
      )}
    </div>
  );
}
