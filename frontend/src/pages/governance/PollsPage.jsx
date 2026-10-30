import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControl,
  FormControlLabel, IconButton, LinearProgress, MenuItem, Radio, RadioGroup, Stack, TextField, Typography,
} from "@mui/material";
import { Add, Delete } from "@mui/icons-material";
import { governanceApi } from "../../api/governanceApi";
import { buildingsApi } from "../../api/buildingsApi";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";

const OUTCOME_COLOR = { passed: "success", no_majority: "warning", no_quorum: "warning", no_votes: "default" };

function Results({ results, t }) {
  const max = Math.max(1, results.votes_cast);
  return (
    <Stack spacing={1} sx={{ mt: 1 }} data-testid="poll-results">
      {results.options.map((o) => (
        <Box key={o.id}>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" fontWeight={o.id === results.winning_option_id ? 700 : 400}>{o.text}</Typography>
            <Typography variant="body2">{o.votes}</Typography>
          </Stack>
          <LinearProgress variant="determinate" value={(100 * o.votes) / max} color={o.id === results.winning_option_id ? "success" : "primary"} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      ))}
      <Typography variant="caption" color="text.secondary">
        {t("turnout", { cast: results.votes_cast, eligible: results.eligible_units, pct: results.turnout_percent })}
      </Typography>
    </Stack>
  );
}

function PollCard({ poll, isAdmin, onChanged, t }) {
  const [choice, setChoice] = useState({});
  const [error, setError] = useState(null);
  const mine = Object.fromEntries((poll.my_votes ?? []).map((v) => [v.apartment_id, v.option_id]));

  const vote = async (unitId) => {
    setError(null);
    try {
      await governanceApi.vote(poll.id, unitId, choice[unitId] ?? mine[unitId]);
      onChanged();
    } catch (err) {
      setError(err.response?.data?.detail || t("error"));
    }
  };
  const close = async () => {
    await governanceApi.closePoll(poll.id);
    onChanged();
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Box>
            <Typography variant="h6" fontWeight={700}>{poll.title}</Typography>
            <Typography variant="caption" color="text.secondary">
              {poll.building_name} · {t("closes")} {new Date(poll.closes_at).toLocaleString()}
            </Typography>
          </Box>
          <Chip size="small" color={poll.is_open ? "info" : "default"} label={poll.is_open ? t("open") : t("closed")} />
        </Stack>
        {poll.description && <Typography sx={{ mt: 1 }}>{poll.description}</Typography>}
        {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}

        {poll.is_open && (poll.my_units ?? []).map((u) => (
          <Box key={u.id} sx={{ mt: 2 }}>
            <Typography variant="subtitle2">{t("your_vote_for_unit", { unit: u.unit_number })}</Typography>
            <FormControl>
              <RadioGroup value={choice[u.id] ?? mine[u.id] ?? ""} onChange={(e) => setChoice((c) => ({ ...c, [u.id]: e.target.value }))}>
                {poll.options.map((o) => <FormControlLabel key={o.id} value={o.id} control={<Radio />} label={o.text} />)}
              </RadioGroup>
            </FormControl>
            <Box>
              <Button variant="contained" size="small" disabled={!(choice[u.id] ?? mine[u.id])} onClick={() => vote(u.id)} sx={{ minHeight: 40 }}>
                {mine[u.id] ? t("change_vote") : t("vote")}
              </Button>
              {mine[u.id] && <Chip size="small" color="success" label={t("voted")} sx={{ ms: 1, marginInlineStart: 1 }} />}
            </Box>
          </Box>
        ))}

        {poll.results && (
          <Box sx={{ mt: 2 }}>
            {!poll.is_open && (
              <Chip color={OUTCOME_COLOR[poll.results.outcome]} label={t(`outcome_${poll.results.outcome}`)} sx={{ mb: 1 }} />
            )}
            <Results results={poll.results} t={t} />
          </Box>
        )}
        {poll.is_open && !isAdmin && <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>{t("results_after_close")}</Typography>}
        {poll.is_open && isAdmin && (
          <Button color="warning" onClick={close} sx={{ mt: 1, minHeight: 40 }}>{t("close_now")}</Button>
        )}
      </CardContent>
    </Card>
  );
}

function NewPollDialog({ open, onClose, onCreated, buildings, t }) {
  const [form, setForm] = useState({ title: "", description: "", options: ["", ""], closes_at: "", quorum_percent: 0, majority: "simple" });
  const [buildingId, setBuildingId] = useState("");
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && !buildingId && buildings[0]) setBuildingId(buildings[0].id);
  }, [open, buildings, buildingId]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const options = form.options.map((o) => o.trim()).filter(Boolean);

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      await governanceApi.createPoll({
        building_id: buildingId, title: form.title, description: form.description, options,
        closes_at: new Date(form.closes_at).toISOString(), quorum_percent: Number(form.quorum_percent) || 0, majority: form.majority,
      });
      setForm({ title: "", description: "", options: ["", ""], closes_at: "", quorum_percent: 0, majority: "simple" });
      onCreated();
    } catch (err) {
      const d = err.response?.data;
      setError(d?.detail || Object.values(d?.errors ?? d ?? {}).flat().join(" ") || t("error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{t("new_poll")}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          {buildings.length > 1 && (
            <TextField select label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)}>
              {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
            </TextField>
          )}
          <TextField label={t("question")} value={form.title} onChange={(e) => set("title", e.target.value)} />
          <TextField label={t("details")} value={form.description} onChange={(e) => set("description", e.target.value)} multiline minRows={2} />
          {form.options.map((o, i) => (
            <Stack key={i} direction="row" spacing={1}>
              <TextField fullWidth size="small" label={t("option_n", { n: i + 1 })} value={o}
                onChange={(e) => set("options", form.options.map((x, j) => (j === i ? e.target.value : x)))} />
              {form.options.length > 2 && (
                <IconButton onClick={() => set("options", form.options.filter((_, j) => j !== i))} aria-label={t("remove_option")}><Delete /></IconButton>
              )}
            </Stack>
          ))}
          {form.options.length < 10 && (
            <Button startIcon={<Add />} onClick={() => set("options", [...form.options, ""])} sx={{ alignSelf: "flex-start" }}>{t("add_option")}</Button>
          )}
          <TextField type="datetime-local" label={t("closes")} value={form.closes_at} onChange={(e) => set("closes_at", e.target.value)} InputLabelProps={{ shrink: true }} />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField type="number" label={t("quorum")} helperText={t("quorum_help")} value={form.quorum_percent} onChange={(e) => set("quorum_percent", e.target.value)} inputProps={{ min: 0, max: 100 }} fullWidth />
            <TextField select label={t("majority")} value={form.majority} onChange={(e) => set("majority", e.target.value)} fullWidth>
              <MenuItem value="simple">{t("majority_simple")}</MenuItem>
              <MenuItem value="two_thirds">{t("majority_two_thirds")}</MenuItem>
            </TextField>
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} sx={{ minHeight: 44 }}>{t("cancel")}</Button>
        <Button variant="contained" disabled={saving || !form.title || options.length < 2 || !form.closes_at || !buildingId} onClick={submit} sx={{ minHeight: 44 }}>
          {t("create")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/** تصويت — the building decides together: one vote per unit, results once it closes. */
export default function PollsPage() {
  const { t } = useTranslation("governance");
  const { isAdmin } = useAuth();
  const [polls, setPolls] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await governanceApi.polls({ page_size: 100 });
      setPolls(res.data?.results ?? res.data ?? []);
    } catch {
      setPolls([]);
    }
  }, []);

  useEffect(() => {
    load();
    if (isAdmin) buildingsApi.list({ page_size: 50 }).then((r) => setBuildings(r.data?.results ?? r.data ?? [])).catch(() => {});
  }, [load, isAdmin]);

  return (
    <>
      <PrivateSEO title="3maracom – Votes" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Typography variant="h5" fontWeight={700}>{t("title")}</Typography>
          {isAdmin && (
            <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)} sx={{ minHeight: 44 }}>{t("new_poll")}</Button>
          )}
        </Stack>
        {polls.length === 0 ? (
          <Typography color="text.secondary">{t("empty")}</Typography>
        ) : (
          <Stack spacing={2}>
            {polls.map((p) => <PollCard key={p.id} poll={p} isAdmin={isAdmin} onChanged={load} t={t} />)}
          </Stack>
        )}
      </Box>
      <NewPollDialog open={dialogOpen} onClose={() => setDialogOpen(false)} onCreated={() => { setDialogOpen(false); load(); }} buildings={buildings} t={t} />
    </>
  );
}
