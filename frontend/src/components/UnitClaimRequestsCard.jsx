import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { apartmentsApi } from "../api/apartmentsApi";
import { useAuth } from "../hooks/useAuth";

/**
 * Admin: residents asking to become owners of a unit (approve / reject).
 * Resident: a notice that their request is waiting for the building admin.
 */
export default function UnitClaimRequestsCard() {
  const { t } = useTranslation("dashboard");
  const { isAdmin } = useAuth();
  const [requests, setRequests] = useState([]);

  const load = useCallback(async () => {
    try {
      const res = await apartmentsApi.claimRequests({ status: "pending" });
      setRequests(res.data?.results ?? res.data ?? []);
    } catch {
      setRequests([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const review = async (fn, id) => {
    await fn(id);
    load();
  };

  if (requests.length === 0) return null;

  if (!isAdmin) {
    return (
      <Alert severity="info" sx={{ mb: 3 }} data-testid="claim-waiting">
        {t("claim_req_waiting", { unit: requests[0].unit_number, building: requests[0].building_name })}
      </Alert>
    );
  }

  return (
    <Card sx={{ mb: 3, border: "2px solid", borderColor: "info.main" }} data-testid="claim-requests">
      <CardContent>
        <Typography variant="h6" gutterBottom>{t("claim_req_title", { count: requests.length })}</Typography>
        <Stack spacing={1.5}>
          {requests.map((r) => (
            <Stack key={r.id} direction={{ xs: "column", sm: "row" }} spacing={1} alignItems={{ sm: "center" }} justifyContent="space-between">
              <Typography>
                <strong>{r.user_name || r.user_email}</strong> — {r.building_name} / {r.unit_number}
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button variant="contained" color="success" sx={{ minHeight: 44 }} onClick={() => review(apartmentsApi.approveClaimRequest, r.id)}>
                  {t("claim_req_approve")}
                </Button>
                <Button variant="outlined" color="error" sx={{ minHeight: 44 }} onClick={() => review(apartmentsApi.rejectClaimRequest, r.id)}>
                  {t("claim_req_reject")}
                </Button>
              </Stack>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
