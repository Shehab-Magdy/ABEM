import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box, CircularProgress, InputAdornment, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableFooter, TableHead,
  TablePagination, TableRow, TableSortLabel, TextField, Typography, useMediaQuery,
} from "@mui/material";
import { Search } from "@mui/icons-material";

/**
 * The one table used across the app: plain MUI Table with search, click-to-sort headers and pagination.
 *
 * columns: [{ id, label, render?(row), sortValue?(row), searchValue?(row), align?, sortable?, searchable?,
 *             hideOnMobile?, width?, cellSx? }]
 *   - sortable defaults to true (sorts by `sortValue(row)` or `row[id]`); set `sortable: false` for action columns.
 *   - searchable defaults to true for sortable columns; `searchValue` overrides what text is matched.
 * Client mode (default): the component searches, sorts and paginates `rows`.
 * Server mode: pass `total` (+ `page`, `rowsPerPage`, `onPageChange`, `onRowsPerPageChange`). `rows` is then the current
 *   page only. Search and sorting stay client-side over that page unless the page also passes `onSearchChange`
 *   and/or `sort`/`onSortChange` (then those are controlled by the parent, who sends them to the API; `onSearchChange` is
 *   debounced 400ms and the table calls onPageChange(0) after a search or sort change).
 * Other props: footer (a <TableRow> for totals, shown under the body), rowKey (string | fn), toolbar (extra filters node), searchable, searchPlaceholder, initialSort
 *   ({id, direction}), pageSizeOptions, defaultRowsPerPage, pagination (false hides it, all rows shown), loading,
 *   emptyMessage, id (on the TableContainer; tutorial anchors), testId (on the <table> element), onRowClick, rowProps(row), size, minWidth.
 */
const collator = {};
const getCollator = (lang) => (collator[lang] ??= new Intl.Collator(lang, { numeric: true, sensitivity: "base" }));

const toDate = (v) => {
  if (v instanceof Date) return v.getTime();
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}/.test(v)) {
    const ms = Date.parse(v);
    return Number.isNaN(ms) ? null : ms;
  }
  return null;
};

export const compareValues = (a, b, lang) => {
  const aEmpty = a === null || a === undefined || a === "";
  const bEmpty = b === null || b === undefined || b === "";
  if (aEmpty || bEmpty) return aEmpty === bEmpty ? 0 : aEmpty ? 1 : -1; // empties always last (handled by caller for desc)
  if (typeof a === "number" && typeof b === "number") return a - b;
  if (typeof a === "boolean" && typeof b === "boolean") return Number(a) - Number(b);
  const da = toDate(a);
  const db = toDate(b);
  if (da !== null && db !== null) return da - db;
  return getCollator(lang).compare(String(a), String(b));
};

const normalize = (v) =>
  String(v ?? "")
    .toLocaleLowerCase()
    .replace(/[ً-ٰٟ]/g, "") // Arabic diacritics
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660)) // Arabic-Indic digits
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x06f0));

const cellText = (col, row) => {
  if (col.searchValue) return col.searchValue(row);
  const v = col.sortValue ? col.sortValue(row) : row[col.id];
  return typeof v === "object" ? "" : v;
};

export default function DataTable({
  columns, rows = [], rowKey = "id", toolbar, searchable = true, searchPlaceholder, initialSort,
  pageSizeOptions = [10, 25, 50], defaultRowsPerPage, pagination = true, loading = false, emptyMessage,
  footer, id, testId, onRowClick, rowProps, size = "medium", minWidth = 560, ariaLabel,
  // server mode
  total, page: pageProp, rowsPerPage: rowsPerPageProp, onPageChange, onRowsPerPageChange,
  search: searchProp, onSearchChange, sort: sortProp, onSortChange,
}) {
  const { t, i18n } = useTranslation("common");
  const lang = i18n.language?.startsWith("ar") ? "ar" : "en";
  const isMobile = useMediaQuery((theme) => theme.breakpoints.down("sm"));
  const serverMode = total !== undefined;

  const [searchLocal, setSearchLocal] = useState("");
  const [sortLocal, setSortLocal] = useState(initialSort ?? null);
  const [pageLocal, setPageLocal] = useState(0);
  const [rppLocal, setRppLocal] = useState(defaultRowsPerPage ?? pageSizeOptions[0]);

  const clientSearch = !onSearchChange;
  const clientSort = !onSortChange;
  const search = searchLocal;
  // Server search: the box stays responsive and the parent is told after the user pauses typing.
  useEffect(() => {
    if (!onSearchChange || searchLocal === (searchProp ?? "")) return undefined;
    const timer = setTimeout(() => {
      onSearchChange(searchLocal);
      if (onPageChange) onPageChange(0);
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchLocal]);
  const sort = clientSort ? sortLocal : sortProp;
  const page = serverMode ? (pageProp ?? 0) : pageLocal;
  const rowsPerPage = serverMode ? (rowsPerPageProp ?? rppLocal) : rppLocal;

  const visibleCols = columns.filter((c) => !(isMobile && c.hideOnMobile));
  const isSortable = (c) => c.sortable ?? true;

  // A new search or a shrinking data set must not leave us on a page that no longer exists.
  useEffect(() => {
    if (!serverMode) setPageLocal(0);
  }, [searchLocal, sortLocal, serverMode, rows.length]);

  const processed = useMemo(() => {
    let out = rows;
    const q = normalize(search).trim();
    if (q && clientSearch) {
      const cols = columns.filter((c) => c.searchable ?? (isSortable(c) || !!c.searchValue));
      out = out.filter((r) => cols.some((c) => normalize(cellText(c, r)).includes(q)));
    }
    if (sort && clientSort) {
      const col = columns.find((c) => c.id === sort.id);
      if (col) {
        const dir = sort.direction === "desc" ? -1 : 1;
        const val = (r) => (col.sortValue ? col.sortValue(r) : r[col.id]);
        out = [...out].sort((a, b) => {
          const va = val(a);
          const vb = val(b);
          const aEmpty = va === null || va === undefined || va === "";
          const bEmpty = vb === null || vb === undefined || vb === "";
          if (aEmpty || bEmpty) return aEmpty === bEmpty ? 0 : aEmpty ? 1 : -1; // empties last in both directions
          return dir * compareValues(va, vb, lang);
        });
      }
    }
    return out;
  }, [rows, columns, search, sort, lang, clientSearch, clientSort]);

  const count = serverMode ? total : processed.length;
  const shown = serverMode || !pagination ? processed : processed.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const handleSort = (colId) => {
    const next = sort?.id === colId && sort.direction === "asc" ? { id: colId, direction: "desc" } : { id: colId, direction: "asc" };
    if (onSortChange) {
      onSortChange(next);
      if (serverMode && onPageChange) onPageChange(0);
    } else setSortLocal(next);
  };
  const handleSearch = (v) => {
    setSearchLocal(v);
  };
  const handlePage = (_, p) => (serverMode ? onPageChange?.(p) : setPageLocal(p));
  const handleRpp = (e) => {
    const v = parseInt(e.target.value, 10);
    if (serverMode) onRowsPerPageChange?.(v);
    else {
      setRppLocal(v);
      setPageLocal(0);
    }
  };

  const keyOf = (r, i) => (typeof rowKey === "function" ? rowKey(r) : r[rowKey] ?? i);
  const showToolbar = searchable || toolbar;

  return (
    <Paper variant="outlined" sx={{ overflow: "hidden" }}>
      {showToolbar && (
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ p: 1.5, alignItems: { sm: "center" }, flexWrap: "wrap" }}>
          {searchable && (
            <TextField
              size="small"
              type="search"
              value={searchLocal}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder={searchPlaceholder ?? t("table_search")}
              slotProps={{
                htmlInput: { "aria-label": searchPlaceholder ?? t("table_search"), "data-testid": testId ? `${testId}-search` : "table-search" },
                input: { startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> },
              }}
              sx={{ minWidth: { sm: 260 }, flexGrow: { xs: 1, sm: 0 }, "& .MuiInputBase-root": { minHeight: 44 } }}
            />
          )}
          {toolbar && <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap", alignItems: "center", flexGrow: 1 }}>{toolbar}</Box>}
        </Stack>
      )}

      <TableContainer id={id} sx={{ overflowX: "auto", position: "relative" }}>
        <Table size={size} sx={{ minWidth }} aria-label={ariaLabel} data-testid={testId}>
          <TableHead>
            <TableRow>
              {visibleCols.map((c) => (
                <TableCell
                  key={c.id}
                  align={c.align}
                  sortDirection={sort?.id === c.id ? sort.direction : false}
                  sx={{
                    fontWeight: 700, whiteSpace: "nowrap", bgcolor: "action.hover", width: c.width,
                    borderBottom: 1, borderColor: "divider", minHeight: 44,
                  }}
                >
                  {isSortable(c) ? (
                    <TableSortLabel
                      active={sort?.id === c.id}
                      direction={sort?.id === c.id ? sort.direction : "asc"}
                      onClick={() => handleSort(c.id)}
                      aria-label={`${t("table_sort_by")} ${typeof c.label === "string" ? c.label : c.id}`}
                      sx={{ minHeight: 44 }}
                    >
                      {c.label}
                    </TableSortLabel>
                  ) : (
                    c.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={visibleCols.length} align="center" sx={{ py: 5 }}>
                  <CircularProgress size={28} aria-label={t("loading")} />
                </TableCell>
              </TableRow>
            ) : shown.length === 0 ? (
              <TableRow>
                <TableCell colSpan={visibleCols.length} align="center" sx={{ py: 5 }}>
                  <Typography color="text.secondary">{emptyMessage ?? t("table_no_results")}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              shown.map((r, i) => (
                <TableRow
                  key={keyOf(r, i)}
                  hover
                  onClick={onRowClick ? () => onRowClick(r) : undefined}
                  sx={{ cursor: onRowClick ? "pointer" : undefined, "&:last-child td": { borderBottom: 0 } }}
                  {...(rowProps ? rowProps(r) : {})}
                >
                  {visibleCols.map((c) => (
                    <TableCell key={c.id} align={c.align} sx={c.cellSx}>
                      {c.render ? c.render(r) : r[c.id]}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
          {footer && <TableFooter>{footer}</TableFooter>}
        </Table>
      </TableContainer>

      {pagination && (
        <TablePagination
          component="div"
          count={count}
          page={Math.min(page, Math.max(0, Math.ceil(count / rowsPerPage) - 1))}
          rowsPerPage={rowsPerPage}
          rowsPerPageOptions={pageSizeOptions}
          onPageChange={handlePage}
          onRowsPerPageChange={handleRpp}
          labelRowsPerPage={t("rows_per_page")}
          labelDisplayedRows={({ from, to, count: c }) => t("table_displayed_rows", { from, to, count: c })}
          getItemAriaLabel={(type) => t(`table_${type}_page`)}
          sx={{ borderTop: 1, borderColor: "divider", "& .MuiTablePagination-toolbar": { flexWrap: "wrap", minHeight: 52 } }}
        />
      )}
    </Paper>
  );
}
