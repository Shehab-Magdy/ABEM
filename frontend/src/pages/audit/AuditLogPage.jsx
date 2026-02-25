/**
 * Audit Log — Sprint 8.
 * Admin-only page displaying the immutable audit log with filters and data exports.
 */
import { useEffect, useState, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  ChevronLeft,
  ChevronRight,
  CloudDownload,
  FilterAlt,
} from "@mui/icons-material";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../hooks/useAuth";

const ENTITY_OPTIONS = ["", "expense", "payment", "user", "building", "apartment"];
const PAGE_SIZE = 20;

export default function AuditLogPage() {
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
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);
  const [page, setPage] = useState(1);
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
          setNextUrl(null);
          setPrevUrl(null);
        } else {
          setLogs(data.results ?? []);
          setCount(data.count ?? 0);
          setNextUrl(data.next ?? null);
          setPrevUrl(data.previous ?? null);
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load audit logs.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const buildUrl = useCallback(
    (pageNum, filters) => {
      const params = new URLSearchParams();
      if (filters.entity)   params.set("entity", filters.entity);
      if (filters.action)   params.set("action", filters.action);
      if (filters.dateFrom) params.set("date_from", filters.dateFrom);
      if (filters.dateTo)   params.set("date_to", filters.dateTo);
      params.set("limit", PAGE_SIZE);
      params.set("offset", (pageNum - 1) * PAGE_SIZE);
      return `/audit/?${params.toString()}`;
    },
    []
  );

  // Initial load and on applied filter change
  useEffect(() => {
    setPage(1);
    fetchPage(buildUrl(1, applied));
  }, [applied, fetchPage, buildUrl]);

  const handleApplyFilters = () => {
    setApplied({
      entity: filterEntity,
      action: filterAction,
      dateFrom: filterDateFrom,
      dateTo: filterDateTo,
    });
  };

  const handleNext = () => {
    if (nextUrl) {
      fetchPage(nextUrl);
      setPage((p) => p + 1);
    }
  };

  const handlePrev = () => {
    if (prevUrl) {
      fetchPage(prevUrl);
      setPage((p) => Math.max(1, p - 1));
    }
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

  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight={700}>
          Audit Log
        </Typography>
        {isAdmin && (
          <Stack direction="row" spacing={1}>
            <Tooltip title="Export Payments CSV">
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudDownload />}
                data-testid="export-csv"
                onClick={() => handleExport("/exports/payments/?file_format=csv", "payments.csv")}
              >
                Payments CSV
              </Button>
            </Tooltip>
            <Tooltip title="Export Payments XLSX">
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudDownload />}
                data-testid="export-xlsx"
                onClick={() => handleExport("/exports/payments/?file_format=xlsx", "payments.xlsx")}
              >
                Payments XLSX
              </Button>
            </Tooltip>
            <Tooltip title="Export Expenses CSV">
              <Button
                variant="outlined"
                size="small"
                startIcon={<CloudDownload />}
                data-testid="export-expenses"
                onClick={() => handleExport("/exports/expenses/?file_format=csv", "expenses.csv")}
              >
                Expenses CSV
              </Button>
            </Tooltip>
          </Stack>
        )}
      </Stack>

      {/* Filter bar */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-end">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Entity</InputLabel>
            <Select
              label="Entity"
              value={filterEntity}
              onChange={(e) => setFilterEntity(e.target.value)}
              inputProps={{ "data-testid": "filter-entity" }}
            >
              {ENTITY_OPTIONS.map((opt) => (
                <MenuItem key={opt} value={opt}>
                  {opt || "All"}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Action"
            size="small"
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            placeholder="e.g. create"
            inputProps={{ "data-testid": "filter-action" }}
            sx={{ minWidth: 130 }}
          />

          <TextField
            label="Date From"
            type="date"
            size="small"
            value={filterDateFrom}
            onChange={(e) => setFilterDateFrom(e.target.value)}
            InputLabelProps={{ shrink: true }}
            inputProps={{ "data-testid": "filter-date-from" }}
          />

          <TextField
            label="Date To"
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
            Apply
          </Button>
        </Stack>
      </Paper>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty state */}
      {!loading && logs.length === 0 && !error && (
        <Box py={6} textAlign="center" data-testid="audit-empty">
          <Typography color="text.secondary">No audit log entries found.</Typography>
        </Box>
      )}

      {/* Table */}
      {!loading && logs.length > 0 && (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small" data-testid="audit-table">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>User Email</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Entity</TableCell>
                <TableCell>Entity ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} data-testid="audit-row">
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    {new Date(log.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>{log.user_email ?? "—"}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell>{log.entity}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>
                    {log.entity_id ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Pagination */}
      {!loading && count > PAGE_SIZE && (
        <Stack
          direction="row"
          justifyContent="center"
          alignItems="center"
          spacing={1}
          mt={2}
          data-testid="audit-pagination"
        >
          <IconButton onClick={handlePrev} disabled={!prevUrl} aria-label="previous page">
            <ChevronLeft />
          </IconButton>
          <Typography variant="body2">
            Page {page} of {totalPages}
          </Typography>
          <IconButton onClick={handleNext} disabled={!nextUrl} aria-label="next page">
            <ChevronRight />
          </IconButton>
        </Stack>
      )}
    </Box>
  );
}
