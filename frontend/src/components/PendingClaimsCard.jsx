import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { paymentsApi } from "../api/paymentsApi";
import { formatCurrency } from "../utils/formatters";

/** Admin: InstaPay transfers residents say they sent, waiting to be confirmed. */
export default function PendingClaimsCard() {
  const { t } = useTranslation("payments");
  const [claims, setClaims] = useState([]);

  const load = useCallback(async () => {
    try {
      const res = await paymentsApi.claims({ status: "pending" });
      // only transfers this person may act on (building admins and the treasurer)
      setClaims((res.data?.results ?? res.data ?? []).filter((c) => c.can_review));
    } catch {
      setClaims([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const review = async (fn, id) => {
    await fn(id);
    load();
  };

  if (claims.length === 0) return null;
  return (
    <Card sx={{ mb: 3, border: "2px solid", borderColor: "warning.main" }} data-testid="pending-claims">
      <CardContent>
        <Typography variant="h6" gutterBottom>{t("claims_title", { count: claims.length })}</Typography>
        <Stack spacing={1.5}>
          {claims.map((c) => (
            <Stack key={c.id} direction={{ xs: "column", sm: "row" }} spacing={1} alignItems={{ sm: "center" }} justifyContent="space-between">
              <Typography>
                {c.building_name} — {c.unit_number}: <strong>{formatCurrency(c.amount)}</strong>
                {c.reference ? ` (${c.reference})` : ""}
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button variant="contained" color="success" sx={{ minHeight: 44 }} onClick={() => review(paymentsApi.confirmClaim, c.id)}>
                  {t("claims_confirm")}
                </Button>
                <Button variant="outlined" color="error" sx={{ minHeight: 44 }} onClick={() => review(paymentsApi.rejectClaim, c.id)}>
                  {t("claims_reject")}
                </Button>
              </Stack>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
