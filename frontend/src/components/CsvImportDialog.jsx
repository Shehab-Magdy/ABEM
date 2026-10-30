import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Link, Stack, Table, TableBody,
  TableCell, TableHead, TableRow, Typography,
} from "@mui/material";
import { UploadFile } from "@mui/icons-material";

/**
 * Bulk import from a CSV file in two steps: check the file (nothing is saved, every row with a problem is listed),
 * then import. Import is all-or-nothing, so a bad file never half-loads.
 * `upload(file, commit)` calls the API and resolves with its { rows, total, errors, created } answer.
 */
export default function CsvImportDialog({ open, title, help, columns, sample, filename, upload, onClose, onDone }) {
  const { t } = useTranslation("common");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      setFile(null);
      setResult(null);
      setError(null);
    }
  }, [open]);

  const run = async (commit) => {
    setBusy(true);
    setError(null);
    try {
      const res = await upload(file, commit);
      setResult(res.data);
      if (commit && res.data.created > 0) onDone(res.data.created);
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? d ?? {}).flat().join(" ") || t("something_went_wrong"));
    } finally {
      setBusy(false);
    }
  };

  const sampleUrl = `data:text/csv;charset=utf-8,${encodeURIComponent(`\ufeff${sample}`)}`;
  const problems = (result?.rows ?? []).filter((r) => !r.ok);

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">{help}</Typography>
          <Typography variant="caption" sx={{ fontFamily: "monospace" }}>{columns}</Typography>
          <Link href={sampleUrl} download={filename} variant="body2">{t("csv_download_sample")}</Link>
          {error && <Alert severity="error">{error}</Alert>}
          <Button component="label" variant="outlined" startIcon={<UploadFile />} sx={{ minHeight: 44 }}>
            {file ? file.name : t("csv_choose_file")}
            <input hidden type="file" accept=".csv,text/csv" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); }} />
          </Button>

          {result && (
            <>
              <Alert severity={result.errors ? "warning" : "success"}>
                {result.created > 0
                  ? t("csv_imported", { n: result.created })
                  : result.errors
                    ? t("csv_has_problems", { errors: result.errors, total: result.total })
                    : t("csv_ready", { n: result.total })}
              </Alert>
              {problems.length > 0 && (
                <Table size="small">
                  <TableHead><TableRow><TableCell>{t("csv_row")}</TableCell><TableCell>{t("csv_problem")}</TableCell></TableRow></TableHead>
                  <TableBody>
                    {problems.slice(0, 50).map((r) => (
                      <TableRow key={r.row}>
                        <TableCell>{r.row}{r.unit_number || r.title ? ` · ${r.unit_number || r.title}` : ""}</TableCell>
                        <TableCell>{r.problems.join(" ")}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("close")}</Button>
        {!(result?.created > 0) && (
          <>
            <Button onClick={() => run(false)} disabled={busy || !file} sx={{ minHeight: 44 }}>{t("csv_check")}</Button>
            <Button variant="contained" onClick={() => run(true)} disabled={busy || !file || !result || result.errors > 0} sx={{ minHeight: 44 }}>
              {busy ? <CircularProgress size={22} color="inherit" /> : t("csv_import")}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
