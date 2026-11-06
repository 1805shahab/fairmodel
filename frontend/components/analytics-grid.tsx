"use client";
import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
  type ColDef,
} from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useMemo, useRef } from "react";
import type { Royalty } from "./types";
import { money, statusLabel } from "./api";

ModuleRegistry.registerModules([AllCommunityModule]);
const theme = themeQuartz.withParams({
  accentColor: "#3563e9",
  backgroundColor: "#ffffff",
  borderColor: "#e8edf5",
  headerBackgroundColor: "#f8fafc",
  fontFamily: "Arial, sans-serif",
  fontSize: 13,
  headerFontSize: 11,
  rowHeight: 54,
  headerHeight: 44,
  wrapperBorder: false,
});
export default function AnalyticsGrid({ rows }: { rows: Royalty[] }) {
  const grid = useRef<AgGridReact<Royalty>>(null);
  const columns = useMemo<ColDef<Royalty>[]>(
    () => [
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
        <span className="small">
          Sort, filter, and compare actual persisted royalty entries.
        </span>
        <button
          className="button secondary small-button"
          onClick={() =>
            grid.current?.api.exportDataAsCsv({
              fileName: "fairmodel-simulated-royalties.csv",
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
