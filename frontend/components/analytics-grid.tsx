"use client";
import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
  colorSchemeDark,
  type ColDef,
} from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useMemo, useRef, useState } from "react";
import type { Royalty } from "./types";
import { money, statusLabel } from "./api";

ModuleRegistry.registerModules([AllCommunityModule]);
const theme = themeQuartz.withPart(colorSchemeDark).withParams({
  accentColor: "#94ddff",
  backgroundColor: "#151d29",
  foregroundColor: "#e1ecf6",
  borderColor: "#2b3749",
  headerBackgroundColor: "#101722",
  headerTextColor: "#a6b7cd",
  rowHoverColor: "#203248",
  fontFamily: '"Segoe UI", sans-serif',
  fontSize: 14,
  headerFontSize: 12,
  rowHeight: 54,
  headerHeight: 44,
  wrapperBorder: false,
});
export default function AnalyticsGrid({ rows }: { rows: Royalty[] }) {
  const grid = useRef<AgGridReact<Royalty>>(null);
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
        valueGetter: (p) => Number(p.data?.amount),
        valueFormatter: (p) => money(p.value, p.data?.currency),
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
        headerName: "RECEIVED · TEST FUNDS",
        valueGetter: (p) => Number(p.data?.received_amount || 0),
        valueFormatter: (p) => money(p.value, p.data?.currency),
        minWidth: 200,
      },
      {
        field: "outstanding_amount",
        headerName: "OUTSTANDING",
        valueGetter: (p) => Number(p.data?.outstanding_amount || 0),
        valueFormatter: (p) => money(p.value, p.data?.currency),
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
      <div className="analytics-grid">
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
            flex: 1,
          }}
          pagination
          paginationPageSize={10}
          paginationPageSizeSelector={[10, 25, 50]}
          getRowId={(p) => p.data.id}
        />
      </div>
    </>
  );
}
