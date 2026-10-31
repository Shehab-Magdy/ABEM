import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";
import { Button, Card, CardContent, LinearProgress, Stack, Typography } from "@mui/material";
import { buildingsApi } from "../api/buildingsApi";
import { formatCurrency } from "../utils/formatters";

/**
 * خزينة العمارة — one read-only card per building showing its current balance.
 * Shown to admins and residents alike.
 */
export default function TreasuryCard() {
  const { t } = useTranslation("dashboard");
  const [rows, setRows] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await buildingsApi.list({ page_size: 50 });
        const buildings = res.data?.results ?? res.data ?? [];
        const treasuries = await Promise.all(
          buildings.map((b) => buildingsApi.treasury(b.id).then((r) => ({ name: b.name, ...r.data }))),
        );
        if (!cancelled) setRows(treasuries);
      } catch {
        if (!cancelled) setRows([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return rows.map((row) => {
    const pct = row.units_billed > 0 ? Math.round((row.units_paid / row.units_billed) * 100) : null;
    return (
      <Card
        key={row.building_id}
        data-testid="treasury-card"
        sx={{
          mb: 3,
          bgcolor: (th) => (th.palette.mode === "dark" ? "primary.dark" : "primary.main"),
          color: "#fff",
        }}
      >
        <CardContent>
          <Typography variant="overline" sx={{ opacity: 0.85 }}>
            {t("treasury_title")} — {row.name}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.85 }}>{t("treasury_balance")}</Typography>
          <Typography variant="h3" fontWeight={800} data-testid="treasury-balance" sx={{ fontVariantNumeric: "tabular-nums" }}>
            {formatCurrency(row.balance)}
          </Typography>
          <Stack direction="row" spacing={3} flexWrap="wrap" useFlexGap sx={{ mt: 1, mb: pct === null ? 0 : 2 }}>
            <Typography variant="caption">{t("treasury_income")}: {formatCurrency(row.total_received)}</Typography>
            <Typography variant="caption">{t("treasury_expenses")}: {formatCurrency(row.total_expenses)}</Typography>
          </Stack>
          {pct !== null && (
            <>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>
                {t("collected_pct", { pct })}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={pct}
                sx={{ height: 12, borderRadius: 6, bgcolor: "rgba(255,255,255,0.25)", "& .MuiLinearProgress-bar": { bgcolor: "#4ADE80" } }}
              />
            </>
          )}
          <Button
            component={RouterLink}
            to="/statement"
            size="small"
            sx={{ mt: 1.5, color: "inherit", textDecoration: "underline", minHeight: 36 }}
          >
            {t("treasury_statement")}
          </Button>
        </CardContent>
      </Card>
    );
  });
}
