import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Box, Button, Card, CardContent, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { buildingsApi } from "../../api/buildingsApi";
import { useAuth } from "../../hooks/useAuth";
import { PrivateSEO } from "../../components/seo/SEO";

/** الهيئة الإدارية — who is chair, treasurer and secretary. Everyone reads; building admins assign. */
export default function BoardPage() {
  const { t } = useTranslation("board");
  const { isAdmin } = useAuth();
  const [buildings, setBuildings] = useState([]);
  const [buildingId, setBuildingId] = useState("");
  const [data, setData] = useState(null);
  const [pick, setPick] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    buildingsApi
      .list({ page_size: 50 })
      .then((res) => {
        const list = res.data?.results ?? res.data ?? [];
        setBuildings(list);
        if (list[0]) setBuildingId(list[0].id);
      })
      .catch(() => setError(t("error")));
  }, [t]);

  const load = useCallback(async () => {
    if (!buildingId) return;
    try {
      setData((await buildingsApi.board(buildingId)).data);
    } catch {
      setError(t("error"));
    }
  }, [buildingId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const assign = async (role, userId) => {
    setError(null);
    try {
      const res = await buildingsApi.setBoardRole(buildingId, userId, role);
      setData(res.data);
      setPick((p) => ({ ...p, [role]: "" }));
    } catch (err) {
      setError(err.response?.data?.detail || t("error"));
    }
  };

  return (
    <>
      <PrivateSEO title="3maracom – Board" />
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        <Typography variant="h5" fontWeight={700} gutterBottom>{t("title")}</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>{t("help")}</Typography>
        {buildings.length > 1 && (
          <TextField select size="small" label={t("building")} value={buildingId} onChange={(e) => setBuildingId(e.target.value)} sx={{ mb: 2, minWidth: 220 }}>
            {buildings.map((b) => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
          </TextField>
        )}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Stack spacing={2}>
          {(data?.board ?? []).map((b) => (
            <Card key={b.role} variant="outlined" data-testid={`board-${b.role}`}>
              <CardContent>
                <Typography variant="subtitle1" fontWeight={700}>{t(`role_${b.role}`)}</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>{t(`role_${b.role}_help`)}</Typography>
                <Typography variant="h6">{b.user_id ? b.name : t("vacant")}</Typography>
                {isAdmin && data?.candidates && (
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1 }}>
                    <TextField select size="small" label={t("choose_member")} value={pick[b.role] ?? ""} onChange={(e) => setPick((p) => ({ ...p, [b.role]: e.target.value }))} sx={{ minWidth: 220 }}>
                      {data.candidates.map((c) => <MenuItem key={c.user_id} value={c.user_id}>{c.name}</MenuItem>)}
                    </TextField>
                    <Button variant="contained" disabled={!pick[b.role]} onClick={() => assign(b.role, pick[b.role])} sx={{ minHeight: 40 }}>{t("assign")}</Button>
                    {b.user_id && <Button color="warning" onClick={() => assign("", b.user_id)} sx={{ minHeight: 40 }}>{t("remove")}</Button>}
                  </Stack>
                )}
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Box>
    </>
  );
}
