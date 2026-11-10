"use client";

import type { ReactNode } from "react";
import Link from "next/link";

export function Metric({
  label,
  value,
  note,
  href,
}: {
  label: string;
  value: ReactNode;
  note?: string;
  href?: string;
}) {
  return (
    <article className="product-metric">
      <span>{label}</span>
      <strong>
        {href ? (
          <Link href={href}>
            {value}
            <span className="sr-only"> — view {label.toLowerCase()}</span>
          </Link>
        ) : (
          value
        )}
      </strong>
      {note && <small>{note}</small>}
    </article>
  );
}

export interface ProductTab {
  id: string;
  label: string;
}
export function Tabs({
  id,
  items,
  value,
  onChange,
}: {
  id: string;
  items: ProductTab[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div
      className="product-tabs"
      role="tablist"
      aria-label="Recording sections"
    >
      {items.map((item, index) => (
        <button
          key={item.id}
          id={`${id}-tab-${item.id}`}
          role="tab"
          aria-selected={value === item.id}
          aria-controls={`${id}-panel-${item.id}`}
          tabIndex={value === item.id ? 0 : -1}
          onClick={() => onChange(item.id)}
          onKeyDown={(event) => {
            const next =
              event.key === "ArrowRight"
                ? (index + 1) % items.length
                : event.key === "ArrowLeft"
                  ? (index - 1 + items.length) % items.length
                  : event.key === "Home"
                    ? 0
                    : event.key === "End"
                      ? items.length - 1
                      : null;
            if (next === null) return;
            event.preventDefault();
            onChange(items[next].id);
            document.getElementById(`${id}-tab-${items[next].id}`)?.focus();
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

export function TabPanel({
  group,
  id,
  active,
  children,
}: {
  group: string;
  id: string;
  active: string;
  children: ReactNode;
}) {
  return (
    <div
      role="tabpanel"
      id={`${group}-panel-${id}`}
      aria-labelledby={`${group}-tab-${id}`}
      hidden={active !== id}
      tabIndex={0}
      className="product-tab-panel"
    >
      {children}
    </div>
  );
}
