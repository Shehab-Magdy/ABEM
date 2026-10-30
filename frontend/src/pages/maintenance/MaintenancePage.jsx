import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Card, CardContent, Chip, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { Add } from "@mui/icons-material";
import { maintenanceApi } from "../../api/maintenanceApi";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";
import ReportIssueDialog from "../../components/ReportIssueDialog";
import WorkOrderDialog from "../../components/WorkOrderDialog";

const STATUSES = ["open", "in_progress", "done"];
const STATUS_COLOR = { open: "warning", in_progress: "info", done: "success" };

export default function MaintenancePage() {
  const { t } = useTranslation("maintenance");
  const { isAdmin } = useAuth();
  const [reports, setReports] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [orderReport, setOrderReport] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await maintenanceApi.list({ page_size: 100 });
      setReports(res.data?.results ?? res.data ?? []);
    } catch {
      setReports([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const changeStatus = async (id, status) => {
    await maintenanceApi.setStatus(id, status);
    load();
  };

  return (
    <>
      <PrivateSEO title="3maracom – Maintenance" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Typography variant="h5" fontWeight={700}>{t("page_title")}</Typography>
          <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)} sx={{ minHeight: 44 }}>
            {t("report_title")}
          </Button>
        </Stack>
        {reports.length === 0 ? (
          <Typography color="text.secondary">{t("empty")}</Typography>
        ) : (
          <Stack spacing={1.5}>
            {reports.map((r) => (
              <Card key={r.id} variant="outlined">
                <CardContent>
                  <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1}>
                    <Box>
                      <Typography fontWeight={700}>{t(`cat_${r.category}`)} — {r.building_name}</Typography>
                      {r.description && <Typography variant="body2">{r.description}</Typography>}
                      <Typography variant="caption" color="text.secondary">
                        {r.reporter_name} · {new Date(r.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                    {r.work_order && (
                      <Box sx={{ mt: 1 }} data-testid="work-order-summary">
                        <Chip size="small" variant="outlined" label={t(`wo_status_${r.work_order.status}`)} sx={{ me: 1, marginInlineEnd: 1 }} />
                        <Typography variant="body2" component="span">
                          {[
                            r.work_order.contractor_name && t("wo_by", { name: r.work_order.contractor_name }),
                            r.work_order.scheduled_on && t("wo_on", { date: r.work_order.scheduled_on }),
                            r.work_order.completed_on && t("wo_done_on", { date: r.work_order.completed_on }),
                            r.work_order.cost && t("wo_cost", { amount: Number(r.work_order.cost).toLocaleString() }),
                          ].filter(Boolean).join(" · ")}
                        </Typography>
                      </Box>
                    )}
                    {r.can_manage && (
                      <Button size="small" variant="outlined" onClick={() => setOrderReport(r)} sx={{ mt: 1, minHeight: 36, alignSelf: "flex-start" }}>
                        {r.work_order ? t("wo_update") : t("wo_take_on")}
                      </Button>
                    )}
                    {isAdmin ? (
                      <TextField select size="small" value={r.status} onChange={(e) => changeStatus(r.id, e.target.value)} sx={{ minWidth: 150 }}>
                        {STATUSES.map((s) => <MenuItem key={s} value={s}>{t(`status_${s}`)}</MenuItem>)}
                      </TextField>
                    ) : (
                      <Chip label={t(`status_${r.status}`)} color={STATUS_COLOR[r.status]} size="small" sx={{ alignSelf: "flex-start" }} />
                    )}
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Box>
      <WorkOrderDialog report={orderReport} onClose={() => setOrderReport(null)} onSaved={() => { setOrderReport(null); load(); }} />
      <ReportIssueDialog open={dialogOpen} onClose={() => setDialogOpen(false)} onSent={load} />
    </>
  );
}
