import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from "@mui/material";
import { maintenanceApi } from "../api/maintenanceApi";
import { operationsApi } from "../api/operationsApi";
import { expensesApi } from "../api/expensesApi";

const STATUSES = ["assigned", "in_progress", "done"];

/** Take a maintenance report on (contractor, date), then follow it: status, completion and the expense it cost. */
export default function WorkOrderDialog({ report, onClose, onSaved }) {
  const { t } = useTranslation("maintenance");
  const order = report?.work_order;
  const [contractors, setContractors] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [form, setForm] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!report) return;
    setError(null);
    setForm({
      contractor_id: order?.contractor_id ?? "", scheduled_on: order?.scheduled_on ?? "", status: order?.status ?? "assigned",
      completed_on: order?.completed_on ?? "", expense_id: order?.expense_id ?? "", notes: order?.notes ?? "",
    });
    operationsApi.contractors({ building_id: report.building_id, page_size: 200 }).then((r) => setContractors(r.data?.results ?? r.data ?? [])).catch(() => {});
    if (order) expensesApi.list({ building_id: report.building_id, kind: "cost", page_size: 100 }).then((r) => setExpenses(r.data?.results ?? r.data ?? [])).catch(() => {});
  }, [report, order]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = { contractor_id: form.contractor_id || null, scheduled_on: form.scheduled_on || null, notes: form.notes };
      if (order) {
        await maintenanceApi.updateWorkOrder(order.id, { ...body, status: form.status, completed_on: form.completed_on || null, expense_id: form.expense_id || null });
      } else {
        await maintenanceApi.createWorkOrder({ ...body, report_id: report.id });
      }
      onSaved();
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? d ?? {}).flat().join(" ") || t("send_error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={!!report} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{order ? t("wo_edit_title") : t("wo_create_title")}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField select label={t("wo_contractor")} value={form.contractor_id ?? ""} onChange={set("contractor_id")} helperText={contractors.length === 0 ? t("wo_no_contractors") : undefined}>
            <MenuItem value="">{t("wo_none")}</MenuItem>
            {contractors.map((c) => <MenuItem key={c.id} value={c.id}>{c.name}{c.trade ? ` — ${c.trade}` : ""}</MenuItem>)}
          </TextField>
          <TextField type="date" label={t("wo_scheduled")} value={form.scheduled_on ?? ""} onChange={set("scheduled_on")} InputLabelProps={{ shrink: true }} />
          {order && (
            <>
              <TextField select label={t("wo_status")} value={form.status} onChange={set("status")}>
                {STATUSES.map((s) => <MenuItem key={s} value={s}>{t(`wo_status_${s}`)}</MenuItem>)}
              </TextField>
              <TextField type="date" label={t("wo_completed")} value={form.completed_on ?? ""} onChange={set("completed_on")} InputLabelProps={{ shrink: true }} />
              <TextField select label={t("wo_expense")} value={form.expense_id ?? ""} onChange={set("expense_id")} helperText={t("wo_expense_help")}>
                <MenuItem value="">{t("wo_none")}</MenuItem>
                {expenses.map((x) => <MenuItem key={x.id} value={x.id}>{x.title} — {x.amount}</MenuItem>)}
              </TextField>
            </>
          )}
          <TextField label={t("wo_notes")} value={form.notes ?? ""} onChange={set("notes")} multiline minRows={2} />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("close")}</Button>
        <Button variant="contained" onClick={save} disabled={busy} sx={{ minHeight: 44 }}>
          {busy ? <CircularProgress size={22} color="inherit" /> : t("wo_save")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
