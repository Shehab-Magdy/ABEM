/**
 * Audit Log — Sprint 8.
 * Admin-only page displaying the immutable audit log with filters and data exports.
 */
import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  CloudDownload,
  FilterAlt,
} from "@mui/icons-material";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../hooks/useAuth";
import DataTable from "../../components/DataTable";
import { PrivateSEO } from "../../components/seo/SEO";

const ENTITY_OPTIONS = ["", "expense", "payment", "user", "building", "apartment"];

export default function AuditLogPage() {
  const { t } = useTranslation("audit");
  const { isAdmin } = useAuth();

  // Filter state
  const [filterEntity, setFilterEntity] = useState("");
  const [filterAction, setFilterAction] = useState("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");

  // Applied filters (only update when "Apply" is clicked)
  const [applied, setApplied] = useState({ entity: "", action: "", dateFrom: "", dateTo: "" });

  // Data state
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchPage = useCallback(
    async (url) => {
      setLoading(true);
      setError("");
      try {
        const resp = await axiosClient.get(url);
        const data = resp.data;
        if (Array.isArray(data)) {
          setLogs(data);
          setCount(data.length);
        } else {
          setLogs(data.results ?? []);
          setCount(data.count ?? 0);
        }
      } catch (err) {
        setError(err.response?.data?.detail || t("load_error", "Failed to load audit logs."));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const buildUrl = useCallback(
    (pageNum, pageSize, filters) => {
      const params = new URLSearchParams();
      if (filters.entity)   params.set("entity", filters.entity);
      if (filters.action)   params.set("action", filters.action);
      if (filters.dateFrom) params.set("date_from", filters.dateFrom);
      if (filters.dateTo)   params.set("date_to", filters.dateTo);
      params.set("page", pageNum + 1);
      params.set("page_size", pageSize);
      return `/audit/?${params.toString()}`;
    },
    []
  );

  // Load on applied-filter, page or page-size change (server-side pagination; page_size is honoured by the API).
  useEffect(() => {
    fetchPage(buildUrl(page, rowsPerPage, applied));
  }, [applied, page, rowsPerPage, fetchPage, buildUrl]);

  const handleApplyFilters = () => {
    setPage(0);
    setApplied({
      entity: filterEntity,
      action: filterAction,
      dateFrom: filterDateFrom,
      dateTo: filterDateTo,
    });
  };

  const handleExport = async (url, filename) => {
    try {
      const resp = await axiosClient.get(url, { responseType: "blob" });
      const blob = new Blob([resp.data]);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch {
      /* best-effort */
    }
  };

  return (
    <>
      <PrivateSEO title="3maracom – Audit Log" />
      <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={700}>
          {t("title")}
        </Typography>
        {isAdmin && (
          <Stack direction="row" spacing={1}>
            <Tooltip title={t("exportPaymentsCsv")}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudDownload />}
                data-testid="export-csv"
                onClick={() => handleExport("/exports/payments/?file_format=csv", "payments.csv")}
              >
                {t("paymentsCsv")}
              </Button>
            </Tooltip>
            <Tooltip title={t("exportExpensesCsv")}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudDownload />}
                data-testid="export-expenses"
                onClick={() => handleExport("/exports/expenses/?file_format=csv", "expenses.csv")}
              >
                {t("expensesCsv")}
              </Button>
            </Tooltip>
          </Stack>
        )}
      </Stack>

      {/* Filter bar */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-end">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t("entity")}</InputLabel>
            <Select
              label={t("entity")}
              value={filterEntity}
              onChange={(e) => setFilterEntity(e.target.value)}
              inputProps={{ "data-testid": "filter-entity" }}
            >
              {ENTITY_OPTIONS.map((opt) => (
                <MenuItem key={opt} value={opt}>
                  {opt || t("all")}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label={t("action")}
            size="small"
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            placeholder="e.g. create"
            inputProps={{ "data-testid": "filter-action" }}
            sx={{ minWidth: 130 }}
          />

          <TextField
            label={t("dateFrom")}
            type="date"
            size="small"
            value={filterDateFrom}
            onChange={(e) => setFilterDateFrom(e.target.value)}
            InputLabelProps={{ shrink: true }}
            inputProps={{ "data-testid": "filter-date-from" }}
          />

          <TextField
            label={t("dateTo")}
            type="date"
            size="small"
            value={filterDateTo}
            onChange={(e) => setFilterDateTo(e.target.value)}
            InputLabelProps={{ shrink: true }}
            inputProps={{ "data-testid": "filter-date-to" }}
          />

          <Button
            variant="contained"
            size="small"
            startIcon={<FilterAlt />}
            data-testid="apply-filters"
            onClick={handleApplyFilters}
          >
            {t("apply")}
          </Button>
        </Stack>
      </Paper>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <DataTable
        id="audit-table"
        testId="audit-table"
        columns={[
          {
            id: "created_at",
            label: t("colTimestamp"),
            sortValue: (log) => log.created_at,
            render: (log) => <span style={{ whiteSpace: "nowrap" }}>{new Date(log.created_at).toLocaleString()}</span>,
          },
          { id: "user_email", label: t("colUserEmail"), render: (log) => log.user_email ?? "—" },
          { id: "action", label: t("colAction") },
          { id: "entity", label: t("colEntity") },
          {
            id: "entity_id",
            label: t("colEntityId"),
            hideOnMobile: true,
            cellSx: { fontFamily: "monospace", fontSize: 12 },
            render: (log) => log.entity_id ?? "—",
          },
        ]}
        rows={logs}
        rowKey="id"
        size="small"
        loading={loading}
        total={count}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={setPage}
        onRowsPerPageChange={(n) => { setRowsPerPage(n); setPage(0); }}
        rowProps={() => ({ "data-testid": "audit-row" })}
        emptyMessage={t("noEntriesFound")}
      />
    </Box>
    </>
  );
}
