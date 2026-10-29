import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, Stack } from "@mui/material";
import { Build, Payments } from "@mui/icons-material";
import PayDuesDialog from "./PayDuesDialog";
import ReportIssueDialog from "./ReportIssueDialog";

/** Big, thumb-friendly shortcuts at the top of the resident home screen. */
export default function QuickActions() {
  const { t } = useTranslation("payments");
  const { t: tm } = useTranslation("maintenance");
  const [payOpen, setPayOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  return (
    <>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mb: 3 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Payments />}
          onClick={() => setPayOpen(true)}
          sx={{ minHeight: 56, flex: 1, fontSize: "1.1rem", fontWeight: 700 }}
          data-testid="pay-dues-btn"
        >
          {t("pay_dues")}
        </Button>
        <Button
          variant="outlined"
          size="large"
          startIcon={<Build />}
          onClick={() => setReportOpen(true)}
          sx={{ minHeight: 56, flex: 1, fontSize: "1.1rem", fontWeight: 700 }}
          data-testid="report-issue-btn"
        >
          {tm("report_title")}
        </Button>
      </Stack>
      <PayDuesDialog open={payOpen} onClose={() => setPayOpen(false)} />
      <ReportIssueDialog open={reportOpen} onClose={() => setReportOpen(false)} />
    </>
  );
}
