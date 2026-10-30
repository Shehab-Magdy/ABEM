import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, Link, MenuItem, Stack, Tab, Table, TableBody, TableCell, TableHead, TableRow, Tabs, TextField, Tooltip, Typography,
} from "@mui/material";
import { Add, Delete, Download, Edit, ExpandMore, UploadFile } from "@mui/icons-material";
import { governanceApi } from "../../api/governanceApi";
import { buildingsApi } from "../../api/buildingsApi";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";
import ConfirmDialog from "../../components/ConfirmDialog";

const KINDS = ["contract", "bylaws", "receipt", "minutes", "other"];
const EMPTY_MEETING = { title: "", held_on: "", attendees: "", agenda: "", notes: "", decisions: "" };

function MeetingDialog({ open, meeting, buildingId, onClose, onSaved, t }) {
  const [form, setForm] = useState(EMPTY_MEETING);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(meeting ? { ...EMPTY_MEETING, ...meeting } : EMPTY_MEETING);
      setError(null);
    }
  }, [open, meeting]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await governanceApi.saveMeeting(meeting?.id, { building_id: buildingId, title: form.title, held_on: form.held_on, attendees: form.attendees, agenda: form.agenda, notes: form.notes, decisions: form.decisions });
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || t("error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm">
      <DialogTitle>{meeting ? t("edit_meeting") : t("new_meeting")}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label={t("meeting_title")} value={form.title} onChange={set("title")} />
          <TextField type="date" label={t("held_on")} value={form.held_on} onChange={set("held_on")} InputLabelProps={{ shrink: true }} />
          <TextField label={t("attendees")} value={form.attendees} onChange={set("attendees")} multiline minRows={2} />
          <TextField label={t("agenda")} value={form.agenda} onChange={set("agenda")} multiline minRows={2} />
          <TextField label={t("notes")} value={form.notes} onChange={set("notes")} multiline minRows={3} />
          <TextField label={t("decisions")} value={form.decisions} onChange={set("decisions")} multiline minRows={3} />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" onClick={save} disabled={busy || !form.title || !form.held_on} sx={{ minHeight: 44 }}>{t("save")}</Button>
      </DialogActions>
    </Dialog>
  );
}

function UploadDialog({ open, buildingId, onClose, onSaved, t }) {
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("other");
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle("");
      setKind("other");
      setFile(null);
      setError(null);
    }
  }, [open]);

  const upload = async () => {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("building_id", buildingId);
      form.append("title", title);
      form.append("kind", kind);
      form.append("file", file);
      await governanceApi.uploadDocument(form);
      onSaved();
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? d ?? {}).flat().join(" ") || t("error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>{t("upload_document")}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label={t("doc_title")} value={title} onChange={(e) => setTitle(e.target.value)} />
          <TextField select label={t("doc_kind")} value={kind} onChange={(e) => setKind(e.target.value)}>
            {KINDS.map((k) => <MenuItem key={k} value={k}>{t(`kind_${k}`)}</MenuItem>)}
          </TextField>
          <Button component="label" variant="outlined" startIcon={<UploadFile />} sx={{ minHeight: 44 }}>
            {file ? file.name : t("choose_file")}
            <input hidden type="file" accept="application/pdf,image/jpeg,image/png" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Button>
          <Typography variant="caption" color="text.secondary">{t("file_help")}</Typography>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" onClick={upload} disabled={busy || !file || !title} sx={{ minHeight: 44 }}>{t("upload")}</Button>
      </DialogActions>
    </Dialog>
  );
}

/** المحاضر والمستندات — meeting minutes and the building's files. Everyone reads; the secretary and admins write. */
export default function RecordsPage() {
  const { t } = useTranslation("records");
  const { isAdmin, user } = useAuth();
  const [tab, setTab] = useState(0);
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [isSecretary, setIsSecretary] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [meetingDialog, setMeetingDialog] = useState({ open: false, meeting: null });
  const [uploadOpen, setUploadOpen] = useState(false);
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
      const [m, d, b] = await Promise.all([
        governanceApi.meetings({ building_id: buildingId, page_size: 100 }),
        governanceApi.documents({ building_id: buildingId, page_size: 100 }),
        buildingsApi.board(buildingId),
      ]);
      setMeetings(m.data?.results ?? m.data ?? []);
      setDocuments(d.data?.results ?? d.data ?? []);
      setIsSecretary((b.data?.board ?? []).some((x) => x.role === "secretary" && x.user_id === user?.id));
    } catch {
      setError(t("error"));
    }
  }, [buildingId, user?.id, t]);

  useEffect(() => {
    load();
  }, [load]);

  const canWrite = isAdmin || isSecretary;

  const downloadPdf = async (meeting) => {
    try {
      const res = await governanceApi.meetingPdf(meeting.id);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `minutes-${meeting.held_on}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(t("pdf_error"));
    }
  };

  const exportAll = async () => {
    try {
      const res = await buildingsApi.exportAll(buildingId);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `building-${buildingId}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(t("export_error"));
    }
  };

  const remove = async () => {
    await (removing.type === "meeting" ? governanceApi.deleteMeeting(removing.id) : governanceApi.deleteDocument(removing.id));
    setRemoving(null);
    load();
  };

  return (
    <>
      <PrivateSEO title="3maracom – Records" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        {buildings.length > 1 && (
          <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 220 }}>
            {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
          </TextField>
        )}
        {isAdmin && buildingId && (
          <Button variant="outlined" startIcon={<Download />} onClick={exportAll} data-testid="export-building" sx={{ mb: 2, minHeight: 44, display: "flex" }}>
            {t("export_building")}
          </Button>
        )}
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label={t("tab_minutes")} />
          <Tab label={t("tab_documents")} />
        </Tabs>

        {tab === 0 && (
          <>
            {canWrite && (
              <Button variant="contained" startIcon={<Add />} onClick={() => setMeetingDialog({ open: true, meeting: null })} sx={{ mb: 2, minHeight: 44 }}>{t("new_meeting")}</Button>
            )}
            {meetings.length === 0 ? <Typography color="text.secondary">{t("no_meetings")}</Typography> : meetings.map((m) => (
              <Accordion key={m.id} disableGutters>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box>
                    <Typography fontWeight={700}>{m.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{m.held_on}</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1.5}>
                    {["attendees", "agenda", "notes", "decisions"].filter((k) => m[k]).map((k) => (
                      <Box key={k}>
                        <Typography variant="subtitle2" color="primary">{t(k)}</Typography>
                        <Typography sx={{ whiteSpace: "pre-line" }}>{m[k]}</Typography>
                      </Box>
                    ))}
                    <Stack direction="row" spacing={1}>
                      <Button size="small" startIcon={<Download />} onClick={() => downloadPdf(m)} sx={{ minHeight: 36 }}>PDF</Button>
                      {canWrite && (
                        <>
                          <Button size="small" startIcon={<Edit />} onClick={() => setMeetingDialog({ open: true, meeting: m })} sx={{ minHeight: 36 }}>{t("edit")}</Button>
                          <Button size="small" color="error" startIcon={<Delete />} onClick={() => setRemoving({ type: "meeting", id: m.id, name: m.title })} sx={{ minHeight: 36 }}>{t("delete")}</Button>
                        </>
                      )}
                    </Stack>
                  </Stack>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {tab === 1 && (
          <>
            {canWrite && (
              <Button variant="contained" startIcon={<UploadFile />} onClick={() => setUploadOpen(true)} sx={{ mb: 2, minHeight: 44 }}>{t("upload_document")}</Button>
            )}
            {documents.length === 0 ? <Typography color="text.secondary">{t("no_documents")}</Typography> : (
              <Table size="small">
                <TableHead><TableRow><TableCell>{t("doc_title")}</TableCell><TableCell>{t("doc_kind")}</TableCell><TableCell>{t("date")}</TableCell><TableCell /></TableRow></TableHead>
                <TableBody>
                  {documents.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell><Link href={d.url} target="_blank" rel="noopener noreferrer">{d.title}</Link></TableCell>
                      <TableCell>{t(`kind_${d.kind}`)}</TableCell>
                      <TableCell>{new Date(d.created_at).toLocaleDateString()}</TableCell>
                      <TableCell align="right">
                        {canWrite && (
                          <Tooltip title={t("delete")}>
                            <IconButton color="error" onClick={() => setRemoving({ type: "document", id: d.id, name: d.title })} aria-label={t("delete")}><Delete /></IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </>
        )}
      </Box>
      <MeetingDialog open={meetingDialog.open} meeting={meetingDialog.meeting} buildingId={buildingId} onClose={() => setMeetingDialog({ open: false, meeting: null })} onSaved={() => { setMeetingDialog({ open: false, meeting: null }); load(); }} t={t} />
      <UploadDialog open={uploadOpen} buildingId={buildingId} onClose={() => setUploadOpen(false)} onSaved={() => { setUploadOpen(false); load(); }} t={t} />
      <ConfirmDialog open={!!removing} title={t("delete_title")} text={t("delete_text", { name: removing?.name })} confirmLabel={t("delete")} onClose={() => setRemoving(null)} onConfirm={remove} />
    </>
  );
}
