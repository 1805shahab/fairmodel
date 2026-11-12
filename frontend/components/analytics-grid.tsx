"use client";
import { money } from "./display-money";

import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
  type ColDef,
} from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import * as Dialog from "@radix-ui/react-dialog";
import type { Royalty } from "./types";
import { statusLabel } from "./api";

ModuleRegistry.registerModules([AllCommunityModule]);
const theme = themeQuartz.withParams({
  accentColor: "var(--accent)",
  backgroundColor: "var(--surface)",
  foregroundColor: "var(--ink)",
  borderColor: "var(--border)",
  headerBackgroundColor: "var(--surface-subtle)",
  headerTextColor: "var(--muted)",
  rowHoverColor: "var(--surface-subtle)",
  fontFamily: "var(--font-ui)",
  fontSize: 14,
  headerFontSize: 12,
  rowHeight: 54,
  headerHeight: 44,
  wrapperBorder: false,
});
export default function AnalyticsGrid({ rows }: { rows: Royalty[] }) {
  const grid = useRef<AgGridReact<Royalty>>(null);
  const container = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<Royalty | null>(null);
  const [search, setSearch] = useState("");
  const columns = useMemo<ColDef<Royalty>[]>(
    () => [
      { field: "artist_name", headerName: "ARTIST", minWidth: 160 },
      { field: "studio_name", headerName: "STUDIO", minWidth: 170 },
      { field: "campaign_name", headerName: "CAMPAIGN", minWidth: 220 },
      { field: "license_title", headerName: "LICENSE", minWidth: 220 },
      {
        field: "compliance_status",
        headerName: "LAST COMPLIANCE",
        minWidth: 190,
      },
      { field: "invoice_status", headerName: "INVOICE STATUS", minWidth: 170 },
      {
        field: "payment_provider",
        headerName: "PAYMENT PROVIDER",
        minWidth: 170,
      },
      {
        field: "id",
        headerName: "ROYALTY ID",
        valueFormatter: (p) => p.value?.slice(0, 10),
        minWidth: 140,
      },
      {
        field: "created_at",
        headerName: "DATE",
        valueFormatter: (p) =>
          new Date(p.value).toLocaleDateString("en", {
            timeZone: "Asia/Karachi",
          }),
        minWidth: 140,
      },
      {
        field: "currency",
        headerName: "CURRENCY",
        width: 120,
        minWidth: 120,
        flex: 0,
      },
      {
        field: "amount",
        headerName: "AMOUNT",
        filter: "agNumberColumnFilter",
        filterValueGetter: (p) => Number(p.data?.amount),
        pinned: "right",
        cellClass: "ledger-money",
        comparator: (a: string, b: string) => Number(a) - Number(b),
        valueFormatter: (p) =>
          p.value == null ? "Not recorded" : money(p.value, p.data?.currency),
        minWidth: 140,
      },
      {
        field: "status",
        headerName: "STATUS",
        valueFormatter: (p) => statusLabel(p.value),
        minWidth: 170,
      },
      {
        field: "received_amount",
        filter: "agNumberColumnFilter",
        filterValueGetter: (p) => Number(p.data?.received_amount),
        headerName: "RECEIVED · TEST FUNDS",
        cellClass: "ledger-money",
        comparator: (a: string, b: string) => Number(a) - Number(b),
        valueFormatter: (p) =>
          p.value == null ? "Not recorded" : money(p.value, p.data?.currency),
        minWidth: 200,
      },
      {
        field: "outstanding_amount",
        filter: "agNumberColumnFilter",
        filterValueGetter: (p) => Number(p.data?.outstanding_amount),
        headerName: "OUTSTANDING",
        cellClass: "ledger-money",
        comparator: (a: string, b: string) => Number(a) - Number(b),
        valueFormatter: (p) =>
          p.value == null ? "Not recorded" : money(p.value, p.data?.currency),
        minWidth: 180,
      },
      {
        headerName: "SPEECH (SEC)",
        valueGetter: (p) => Number(p.data?.calculation.spoken_seconds),
        minWidth: 150,
      },
      {
        headerName: "ADDITIONAL (SEC)",
        valueGetter: (p) => Number(p.data?.calculation.additional_seconds),
        minWidth: 180,
      },
      {
        headerName: "BILLING BASIS",
        valueGetter: (p) => p.data?.calculation.billing_basis,
        minWidth: 170,
      },
    ],
    [],
  );
  return (
    <>
      <div className="grid-toolbar">
        <label className="ledger-search">
          Find in ledger
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Artist, studio, campaign or license…"
          />
        </label>
        <button
          className="button secondary small-button"
          onClick={() =>
            grid.current?.api.exportDataAsCsv({
              fileName: "fairmodel-provider-labeled-royalties.csv",
            })
          }
        >
          Export CSV
        </button>
      </div>
      <p className="small">
        Select a ledger row to inspect its recorded calculation and supporting
        audio.
      </p>
      <div className="analytics-grid" ref={container}>
        <AgGridReact
          ref={grid}
          theme={theme}
          rowData={rows}
          quickFilterText={search}
          columnDefs={columns}
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true,
            width: 200,
          }}
          pagination
          ensureDomOrder
          suppressColumnVirtualisation
          suppressRowVirtualisation
          animateRows={false}
          onGridReady={(event) => {
            event.api.setGridAriaProperty("label", "Royalty analytics ledger");
            const viewport = container.current?.querySelector<HTMLElement>(
              ".ag-center-cols-viewport",
            );
            if (viewport) {
              viewport.tabIndex = 0;
            }
          }}
          onRowClicked={(event) => {
            if (event.data) setSelected(event.data);
          }}
          onCellKeyDown={(event) => {
            if (
              (event.event as KeyboardEvent | undefined)?.key === "Enter" &&
              event.data
            )
              setSelected(event.data);
          }}
          paginationPageSize={10}
          paginationPageSizeSelector={[10, 25, 50]}
          getRowId={(p) => p.data.id}
        />
      </div>
      <Dialog.Root
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="workspace-menu-scrim" />
          <Dialog.Content className="workspace-mobile-menu ledger-row-detail">
            <Dialog.Title>
              {selected?.campaign_name || "Royalty calculation"}
            </Dialog.Title>
            <Dialog.Description>
              Read-only evidence for this recorded allocation. No approval or
              payment action is performed here.
            </Dialog.Description>
            {selected && (
              <>
                <p className="ledger-money">
                  {money(selected.amount, selected.currency)}
                </p>
                <p>{selected.license_title}</p>
                <code className="formula">
                  {selected.calculation.explanation}
                </code>
                <span className="provider-badge">
                  {selected.payment_provider === "paypal_sandbox"
                    ? "PayPal Sandbox (test funds)"
                    : selected.payment_provider === "mock"
                      ? "Mock provider"
                      : "No invoice provider recorded"}
                </span>
                <p>
                  <Link
                    className="text-link"
                    href={`/dashboard/submissions/${selected.asset_id}`}
                  >
                    Open recording & evidence ↗
                  </Link>
                </p>
              </>
            )}
            <Dialog.Close className="button secondary">
              Close details
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <div
        className="analytics-mobile"
        aria-label="Royalty ledger, compact view"
      >
        {rows
          .filter((row) =>
            [
              row.artist_name,
              row.studio_name,
              row.campaign_name,
              row.license_title,
            ]
              .join(" ")
              .toLowerCase()
              .includes(search.toLowerCase()),
          )
          .map((row) => (
            <article key={row.id}>
              <span className="eyebrow">
                {row.artist_name} / {row.studio_name}
              </span>
              <h3>
                <a
                  className="text-link"
                  href={`/dashboard/submissions/${row.asset_id}`}
                >
                  {row.campaign_name || "Open recording"} ↗
                </a>
              </h3>
              <p className="ledger-money">{money(row.amount, row.currency)}</p>
              <dl>
                <dt>Agreement</dt>
                <dd>{row.license_title}</dd>
                <dt>Royalty</dt>
                <dd>{statusLabel(row.status)}</dd>
                <dt>Compliance</dt>
                <dd>
                  {row.compliance_status
                    ? statusLabel(row.compliance_status)
                    : "Not evaluated"}
                </dd>
                <dt>Invoice</dt>
                <dd>
                  {row.invoice_status
                    ? statusLabel(row.invoice_status)
                    : "Not invoiced"}
                </dd>
              </dl>
              <span className="provider-badge">
                {row.payment_provider === "paypal_sandbox"
                  ? "PayPal Sandbox (test funds)"
                  : row.payment_provider === "mock"
                    ? "Mock provider"
                    : "No invoice provider recorded"}
              </span>
            </article>
          ))}
      </div>
    </>
  );
}
