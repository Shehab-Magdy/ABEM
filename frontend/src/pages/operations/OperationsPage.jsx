import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem,
  Stack, Tab, Tabs, TextField, Tooltip, Typography,
} from "@mui/material";
import { Add, CheckCircle, Delete, Edit, ErrorOutline, Phone, Schedule } from "@mui/icons-material";
import { operationsApi } from "../../api/operationsApi";
import { buildingsApi } from "../../api/buildingsApi";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";
import ConfirmDialog from "../../components/ConfirmDialog";

const REPEATS = ["none", "monthly", "quarterly", "yearly"];
const daysUntil = (iso) => Math.round((new Date(iso) - new Date(new Date().toDateString())) / 86400000);

function DueChip({ iso, t }) {
  const d = daysUntil(iso);
  if (d < 0) return <Chip size="small" color="error" icon={<ErrorOutline />} label={t("overdue_days", { n: -d })} />;
  if (d <= 14) return <Chip size="small" color="warning" icon={<Schedule />} label={d === 0 ? t("due_today") : t("due_in_days", { n: d })} />;
  return <Chip size="small" variant="outlined" icon={<Schedule />} label={t("due_in_days", { n: d })} />;
}

function FormDialog({ open, title, fields, initial, onClose, onSave, t }) {
  const [form, setForm] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (open) {
      setForm(initial);
      setError(null);
    }
  }, [open, initial]);
  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await onSave(form);
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? d ?? {}).flat().join(" ") || t("error"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {fields.map((f) => (
            <TextField key={f.name} label={f.label} type={f.type || "text"} select={!!f.options} value={form[f.name] ?? ""} multiline={f.multiline} minRows={f.multiline ? 2 : undefined}
              onChange={(e) => setForm((s) => ({ ...s, [f.name]: e.target.value }))} InputLabelProps={f.type === "date" ? { shrink: true } : undefined}>
              {(f.options || []).map((o) => <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>)}
            </TextField>
          ))}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" onClick={save} disabled={busy} sx={{ minHeight: 44 }}>{t("save")}</Button>
      </DialogActions>
    </Dialog>
  );
}

/** العمليات — the building's calendar of recurring obligations and its contractors. */
export default function OperationsPage() {
  const { t } = useTranslation("operations");
  const { isAdmin, user } = useAuth();
  const [tab, setTab] = useState(0);
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [canWrite, setCanWrite] = useState(false);
  const [obligations, setObligations] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [dialog, setDialog] = useState(null); // {type, item}
  const [removing, setRemoving] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    buildingsApi.list({ page_size: 50 }).then((res) => {
      const list = res.data?.results ?? res.data ?? [];
      setBuildings(list);
      if (list[0]) setBuildingId(list[0].id);
    }).catch(() => setError(t("error")));
  }, [t]);

  const load = useCallback(async () => {
    if (!buildingId) return;
    try {
      const [o, c, b] = await Promise.all([
        operationsApi.obligations({ building_id: buildingId, active: "true", page_size: 200 }),
        operationsApi.contractors({ building_id: buildingId, page_size: 200 }),
        buildingsApi.board(buildingId),
      ]);
      setObligations(o.data?.results ?? o.data ?? []);
      setContractors(c.data?.results ?? c.data ?? []);
      setCanWrite(isAdmin || (b.data?.board ?? []).some((x) => x.user_id === user?.id));
    } catch {
      setError(t("error"));
    }
  }, [buildingId, isAdmin, user?.id, t]);

  useEffect(() => {
    load();
  }, [load]);

  const repeatOptions = REPEATS.map((r) => ({ value: r, label: t(`repeat_${r}`) }));
  const contractorOptions = [{ value: "", label: t("no_contractor") }, ...contractors.map((c) => ({ value: c.id, label: c.name }))];

  const obligationFields = [
    { name: "title", label: t("ob_title") },
    { name: "due_date", label: t("due_date"), type: "date" },
    { name: "repeat", label: t("repeat"), options: repeatOptions },
    { name: "contractor_id", label: t("contractor"), options: contractorOptions },
    { name: "remind_days", label: t("remind_days"), type: "number" },
    { name: "notes", label: t("notes"), multiline: true },
  ];
  const contractorFields = [
    { name: "name", label: t("name") }, { name: "trade", label: t("trade") }, { name: "phone", label: t("phone") },
    { name: "contract_start", label: t("contract_start"), type: "date" }, { name: "contract_end", label: t("contract_end"), type: "date" },
    { name: "notes", label: t("notes"), multiline: true },
  ];

  const save = async (form) => {
    const clean = (o) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== "" && v !== undefined));
    if (dialog.type === "obligation") {
      await operationsApi.saveObligation(dialog.item?.id, { ...clean(form), building_id: buildingId, contractor_id: form.contractor_id || null, remind_days: Number(form.remind_days) || 14 });
    } else {
      await operationsApi.saveContractor(dialog.item?.id, { ...clean(form), building_id: buildingId });
    }
    setDialog(null);
    load();
  };

  const done = async (ob) => {
    try {
      await operationsApi.markDone(ob.id);
      load();
    } catch {
      setError(t("error"));
    }
  };

  const remove = async () => {
    await (removing.type === "obligation" ? operationsApi.deleteObligation(removing.id) : operationsApi.deleteContractor(removing.id));
    setRemoving(null);
    load();
  };

  const initial = dialog?.item
    ? { ...dialog.item, contractor_id: dialog.item.contractor_id ?? "" }
    : dialog?.type === "obligation" ? { repeat: "yearly", remind_days: 14 } : {};

  return (
    <>
      <PrivateSEO title="3maracom – Operations" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{t("help")}</Typography>
        {buildings.length > 1 && (
          <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 220 }}>
            {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
          </TextField>
        )}
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label={t("tab_calendar")} /><Tab label={t("tab_contractors")} />
        </Tabs>

        {tab === 0 && (
          <Stack spacing={1.5}>
            {canWrite && <Box><Button variant="contained" startIcon={<Add />} onClick={() => setDialog({ type: "obligation", item: null })} sx={{ minHeight: 44 }}>{t("add_obligation")}</Button></Box>}
            {obligations.length === 0 && <Typography color="text.secondary">{t("no_obligations")}</Typography>}
            {obligations.map((o) => (
              <Card key={o.id} variant="outlined" data-testid="obligation">
                <CardContent>
                  <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1}>
                    <Box>
                      <Typography fontWeight={700}>{o.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {o.due_date} · {t(`repeat_${o.repeat}`)}{o.contractor_name ? ` · ${o.contractor_name}` : ""}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                      <DueChip iso={o.due_date} t={t} />
                      {canWrite && (
                        <>
                          <Button size="small" variant="outlined" color="success" startIcon={<CheckCircle />} onClick={() => done(o)} sx={{ minHeight: 36 }}>{t("mark_done")}</Button>
                          <Tooltip title={t("edit")}><IconButton onClick={() => setDialog({ type: "obligation", item: o })} aria-label={t("edit")}><Edit /></IconButton></Tooltip>
                          <Tooltip title={t("delete")}><IconButton color="error" onClick={() => setRemoving({ type: "obligation", id: o.id, name: o.title })} aria-label={t("delete")}><Delete /></IconButton></Tooltip>
                        </>
                      )}
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}

        {tab === 1 && (
          <Stack spacing={1.5}>
            {canWrite && <Box><Button variant="contained" startIcon={<Add />} onClick={() => setDialog({ type: "contractor", item: null })} sx={{ minHeight: 44 }}>{t("add_contractor")}</Button></Box>}
            {contractors.length === 0 && <Typography color="text.secondary">{t("no_contractors")}</Typography>}
            {contractors.map((c) => (
              <Card key={c.id} variant="outlined">
                <CardContent>
                  <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1}>
                    <Box>
                      <Typography fontWeight={700}>{c.name}</Typography>
                      <Typography variant="body2" color="text.secondary">{c.trade}</Typography>
                      {c.contract_end && (
                        <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
                          <Typography variant="caption">{t("contract_until", { date: c.contract_end })}</Typography>
                          <DueChip iso={c.contract_end} t={t} />
                        </Stack>
                      )}
                    </Box>
                    <Stack direction="row" spacing={1} alignItems="center">
                      {c.phone && <Button size="small" variant="outlined" startIcon={<Phone />} href={`tel:${c.phone}`} sx={{ minHeight: 36 }}>{c.phone}</Button>}
                      {canWrite && (
                        <>
                          <Tooltip title={t("edit")}><IconButton onClick={() => setDialog({ type: "contractor", item: c })} aria-label={t("edit")}><Edit /></IconButton></Tooltip>
                          <Tooltip title={t("delete")}><IconButton color="error" onClick={() => setRemoving({ type: "contractor", id: c.id, name: c.name })} aria-label={t("delete")}><Delete /></IconButton></Tooltip>
                        </>
                      )}
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Box>
      <FormDialog open={!!dialog} title={dialog ? t(dialog.item ? `edit_${dialog.type}` : `add_${dialog.type}`) : ""} fields={dialog?.type === "obligation" ? obligationFields : contractorFields} initial={initial} onClose={() => setDialog(null)} onSave={save} t={t} />
      <ConfirmDialog open={!!removing} title={t("delete_title")} text={t("delete_text", { name: removing?.name })} confirmLabel={t("delete")} onClose={() => setRemoving(null)} onConfirm={remove} />
    </>
  );
}
