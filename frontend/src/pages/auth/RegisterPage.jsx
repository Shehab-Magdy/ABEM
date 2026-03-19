/**
 * Multi-step registration wizard.
 *
 * Step 1 (all):         Account details + role selection (Admin | Owner)
 * Step 2 Admin:         Add one or more buildings to manage (can skip)
 * Step 2.5 Admin:       Optionally claim an apartment/store in one of those buildings
 * Step 2 Owner:         Select a building → select an available unit to claim (can skip)
 * Step 3:               Success — redirect to dashboard
 */
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link as RouterLink } from "react-router-dom";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  FormLabel,
  IconButton,
  InputAdornment,
  InputLabel,
  Link,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { Add, Delete, Visibility, VisibilityOff } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { authApi } from "../../api/authApi";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { useAuthStore } from "../../contexts/authStore";
import PhoneInput from "../../components/PhoneInput";
import { PublicSEO } from "../../components/seo/SEO";
import LanguageSwitcher from "../../components/LanguageSwitcher";

// Step label arrays are built inside RegisterPage using t() — see below.

// ── Step 1: Account ────────────────────────────────────────────────────────────

function AccountStep({ onDone, prefillEmail }) {
  const { t } = useTranslation("auth");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { login } = useAuthStore();
  const { register, handleSubmit, watch, control, formState: { errors } } = useForm({
    defaultValues: { role: "owner", email: prefillEmail ?? "" },
  });
  const password = watch("password", "");

  const onSubmit = async (data) => {
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.selfRegister({
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        phone: data.phone || "",
        role: data.role,
        password: data.password,
        confirm_password: data.confirm_password,
      });
      const { access, refresh, user } = res.data;
      login(user, access, refresh);
      onDone(user.role);
    } catch (err) {
      const data = err.response?.data;
      // Backend wraps errors: {"status":"error","code":400,"errors":{field:[msgs]}}
      const errObj = (data && typeof data === "object") ? (data.errors ?? data) : data;
      if (errObj && typeof errObj === "object") {
        setError(Object.values(errObj).flat().join(" "));
      } else {
        setError(errObj || t("errors:server_error"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
      <Stack spacing={2.5}>
        {error && <Alert severity="error">{error}</Alert>}
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField label={t("first_name")} fullWidth autoFocus
            error={!!errors.first_name} helperText={errors.first_name?.message}
            {...register("first_name", { required: t("common:required") })} />
          <TextField label={t("last_name")} fullWidth
            error={!!errors.last_name} helperText={errors.last_name?.message}
            {...register("last_name", { required: t("common:required") })} />
        </Stack>
        <TextField label={t("email_address")} type="email" fullWidth
          error={!!errors.email} helperText={errors.email?.message}
          {...register("email", {
            required: t("common:required"),
            pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: t("errors:invalid_email") },
          })} />
        <Controller
          name="phone"
          control={control}
          defaultValue=""
          rules={{
            validate: (v) => {
              if (!v || v.trim() === "") return true;
              return /^\+?[1-9][\d\s\-().]{6,19}$/.test(v.trim()) || t("errors:invalid_phone");
            },
          }}
          render={({ field }) => (
            <PhoneInput
              label={t("phone_optional")}
              value={field.value}
              onChange={field.onChange}
              error={!!errors.phone}
              helperText={errors.phone?.message || t("phone_helper")}
            />
          )}
        />
        <TextField label={t("password")} type={showPw ? "text" : "password"} fullWidth
          error={!!errors.password}
          helperText={errors.password?.message || t("password_min_length")}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPw((p) => !p)} edge="end" tabIndex={-1}>
                  {showPw ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          {...register("password", { required: t("common:required") })} />
        <TextField label={t("confirm_password")} type={showPw ? "text" : "password"} fullWidth
          error={!!errors.confirm_password} helperText={errors.confirm_password?.message}
          {...register("confirm_password", {
            required: t("common:required"),
            validate: (v) => v === password || t("passwords_dont_match"),
          })} />
        <FormControl component="fieldset">
          <FormLabel>{t("i_am_a")}</FormLabel>
          <Controller
            name="role"
            control={control}
            defaultValue="owner"
            render={({ field }) => (
              <RadioGroup row {...field}>
                <FormControlLabel value="owner" control={<Radio />} label={t("owner_role_label")} />
                <FormControlLabel value="admin" control={<Radio />} label={t("admin_role_label")} />
              </RadioGroup>
            )}
          />
        </FormControl>
        <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
          {loading ? <CircularProgress size={24} color="inherit" /> : t("continue")}
        </Button>
        <Typography variant="body2" align="center" color="text.secondary">
          {t("already_have_account")}{" "}
          <Link component={RouterLink} to="/login" underline="hover">{t("sign_in_link")}</Link>
        </Typography>
      </Stack>
    </Box>
  );
}

// ── Step 2 Admin: Add buildings ────────────────────────────────────────────────

function AdminBuildingsStep({ onDone, onSkip }) {
  const { t } = useTranslation("auth");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const { control, register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      buildings: [{ name: "", address: "", city: "", country: "", num_floors: 1, num_apartments: 0, num_stores: 0 }],
    },
  });
  const { fields, append, remove } = useFieldArray({ control, name: "buildings" });

  const onSubmit = async (data) => {
    setError(null);
    setSubmitting(true);
    try {
      for (const b of data.buildings) {
        if (b.name.trim()) {
          await buildingsApi.create({
            name: b.name,
            address: b.address,
            city: b.city,
            country: b.country || "",
            num_floors: parseInt(b.num_floors, 10) || 1,
            num_apartments: parseInt(b.num_apartments, 10) || 0,
            num_stores: parseInt(b.num_stores, 10) || 0,
          });
        }
      }
      onDone();
    } catch (err) {
      const data = err.response?.data;
      const errObj = (data && typeof data === "object") ? (data.errors ?? data) : data;
      if (errObj && typeof errObj === "object") {
        setError(Object.values(errObj).flat().join(" "));
      } else {
        setError(errObj || t("errors:server_error"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
      <Stack spacing={3}>
        {error && <Alert severity="error">{error}</Alert>}
        <Typography variant="body2" color="text.secondary">
          {t("buildings_step_desc")}
        </Typography>
        {fields.map((field, idx) => (
          <Box key={field.id} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
              <Typography variant="subtitle2" fontWeight={600}>{t("building_number", { num: idx + 1 })}</Typography>
              {fields.length > 1 && (
                <IconButton size="small" color="error" onClick={() => remove(idx)}>
                  <Delete fontSize="small" />
                </IconButton>
              )}
            </Stack>
            <Stack spacing={2}>
              <TextField label={t("buildings:building_name")} fullWidth size="small"
                error={!!errors.buildings?.[idx]?.name} helperText={errors.buildings?.[idx]?.name?.message}
                {...register(`buildings.${idx}.name`, { required: t("common:required") })} />
              <TextField label={t("buildings:address")} fullWidth size="small"
                error={!!errors.buildings?.[idx]?.address} helperText={errors.buildings?.[idx]?.address?.message}
                {...register(`buildings.${idx}.address`, { required: t("common:required") })} />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label={t("buildings:city")} fullWidth size="small"
                  error={!!errors.buildings?.[idx]?.city} helperText={errors.buildings?.[idx]?.city?.message}
                  {...register(`buildings.${idx}.city`, { required: t("common:required") })} />
                <TextField label={t("buildings:country")} fullWidth size="small"
                  {...register(`buildings.${idx}.country`)} />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label={t("buildings:floors")} type="number" size="small" fullWidth
                  inputProps={{ min: 1 }}
                  {...register(`buildings.${idx}.num_floors`)} />
                <TextField label={t("buildings:num_apartments")} type="number" size="small" fullWidth
                  inputProps={{ min: 0 }}
                  helperText={t("auto_apartments_hint")}
                  {...register(`buildings.${idx}.num_apartments`)} />
                <TextField label={t("buildings:num_stores")} type="number" size="small" fullWidth
                  inputProps={{ min: 0 }}
                  helperText={t("auto_stores_hint")}
                  {...register(`buildings.${idx}.num_stores`)} />
              </Stack>
            </Stack>
          </Box>
        ))}
        <Button variant="outlined" startIcon={<Add />} size="small" sx={{ alignSelf: "flex-start" }}
          onClick={() => append({ name: "", address: "", city: "", country: "", num_floors: 1, num_apartments: 0, num_stores: 0 })}>
          {t("add_another_building")}
        </Button>
        <Stack direction="row" spacing={2}>
          <Button variant="outlined" fullWidth onClick={onSkip}>{t("skip_for_now")}</Button>
          <Button type="submit" variant="contained" fullWidth disabled={submitting}>
            {submitting ? <CircularProgress size={22} color="inherit" /> : t("save_continue")}
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}

// ── Shared: Select and claim a unit ───────────────────────────────────────────

function ClaimUnitStep({ onDone, onSkip, isAdmin }) {
  const { t } = useTranslation("auth");
  const [buildings, setBuildings] = useState([]);
  const [apartments, setApartments] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [selectedApartment, setSelectedApartment] = useState("");
  const [unitTypeFilter, setUnitTypeFilter] = useState("all");
  const [loadingBuildings, setLoadingBuildings] = useState(true);
  const [loadingApts, setLoadingApts] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState(null);

  // Registration code entry
  const [regCode, setRegCode] = useState("");
  const [validatingCode, setValidatingCode] = useState(false);
  const [codeInfo, setCodeInfo] = useState(null);
  const [codeError, setCodeError] = useState(null);
  const [claimingCode, setClaimingCode] = useState(false);

  useEffect(() => {
    apartmentsApi.buildingDirectory()
      .then((r) => setBuildings(r.data))
      .catch(() => setError(t("errors:network_error")))
      .finally(() => setLoadingBuildings(false));
  }, []);

  useEffect(() => {
    if (!selectedBuilding) { setApartments([]); return; }
    setLoadingApts(true);
    setSelectedApartment("");
    apartmentsApi.available(selectedBuilding)
      .then((r) => setApartments(r.data))
      .catch(() => setError(t("errors:network_error")))
      .finally(() => setLoadingApts(false));
  }, [selectedBuilding]);

  const handleClaim = async () => {
    if (!selectedApartment) return;
    setError(null);
    setClaiming(true);
    try {
      await apartmentsApi.claim(selectedApartment);
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setClaiming(false);
    }
  };

  const filtered = unitTypeFilter === "all"
    ? apartments
    : apartments.filter((a) => a.type === unitTypeFilter);

  const handleValidateCode = async () => {
    if (!regCode.trim()) return;
    setCodeError(null);
    setCodeInfo(null);
    setValidatingCode(true);
    try {
      const res = await apartmentsApi.validateInvite(undefined, regCode.trim().toUpperCase());
      setCodeInfo(res.data);
    } catch (err) {
      setCodeError(err.response?.data?.detail || t("invalid_code"));
    } finally {
      setValidatingCode(false);
    }
  };

  const handleClaimCode = async () => {
    setClaimingCode(true);
    setCodeError(null);
    try {
      await apartmentsApi.useInviteCode(regCode.trim().toUpperCase());
      onDone();
    } catch (err) {
      setCodeError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setClaimingCode(false);
    }
  };

  if (loadingBuildings) return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      <Typography variant="body2" color="text.secondary">
        {isAdmin
          ? t("claim_unit_admin_desc")
          : t("claim_unit_owner_desc")}
      </Typography>
      {buildings.length === 0 ? (
        <Alert severity="info">
          {t("no_buildings_yet")}{" "}
          {isAdmin
            ? t("add_building_first")
            : t("ask_admin_register")}
        </Alert>
      ) : (
        <>
          <FormControl fullWidth>
            <InputLabel>{t("select_building")}</InputLabel>
            <Select
              label={t("select_building")}
              value={selectedBuilding}
              onChange={(e) => { setSelectedBuilding(e.target.value); setUnitTypeFilter("all"); setSelectedApartment(""); }}
            >
              {buildings.map((b) => (
                <MenuItem key={b.id} value={b.id}>{b.name} — {b.city}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedBuilding && (
            loadingApts ? (
              <Box display="flex" justifyContent="center"><CircularProgress size={28} /></Box>
            ) : apartments.length === 0 ? (
              <Alert severity="info">{t("no_units_available")}</Alert>
            ) : (
              <>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">{t("filter_by_type")}</Typography>
                  <ToggleButtonGroup
                    value={unitTypeFilter}
                    exclusive
                    onChange={(_, v) => { if (v) { setUnitTypeFilter(v); setSelectedApartment(""); } }}
                    size="small"
                  >
                    <ToggleButton value="all">{t("common:all_buildings", "All")}</ToggleButton>
                    <ToggleButton value="apartment">{t("buildings:apartments_title", "Apartments")}</ToggleButton>
                    <ToggleButton value="store">{t("buildings:num_stores", "Stores")}</ToggleButton>
                  </ToggleButtonGroup>
                </Stack>
                {filtered.length === 0 ? (
                  <Alert severity="info">{t("no_units_of_type")}</Alert>
                ) : (
                  <FormControl fullWidth>
                    <InputLabel>{t("select_unit")}</InputLabel>
                    <Select
                      label={t("select_unit")}
                      value={selectedApartment}
                      onChange={(e) => setSelectedApartment(e.target.value)}
                    >
                      {filtered.map((a) => (
                        <MenuItem key={a.id} value={a.id}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                              label={a.type === "store" ? "Store" : "Apt"}
                              size="small"
                              color={a.type === "store" ? "warning" : "primary"}
                              variant="outlined"
                            />
                            <span>
                              Unit {a.unit_number} — Floor {a.floor}
                              {a.size_sqm ? ` — ${a.size_sqm} m²` : ""}
                            </span>
                          </Stack>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              </>
            )
          )}
        </>
      )}
      <Stack direction="row" spacing={2}>
        <Button variant="outlined" fullWidth onClick={onSkip}>{t("skip_for_now")}</Button>
        <Button variant="contained" fullWidth disabled={!selectedApartment || claiming} onClick={handleClaim}>
          {claiming ? <CircularProgress size={22} color="inherit" /> : t("claim_unit")}
        </Button>
      </Stack>

      {/* Registration code alternative */}
      <Divider sx={{ my: 1 }}>
        <Typography variant="caption" color="text.secondary">{t("or_use_code")}</Typography>
      </Divider>
      {codeError && <Alert severity="error" onClose={() => setCodeError(null)}>{codeError}</Alert>}
      {codeInfo && (
        <Alert severity="success">
          Found: <strong>Unit {codeInfo.unit_number}</strong> in <strong>{codeInfo.building_name}</strong>
        </Alert>
      )}
      <Stack direction="row" spacing={1} alignItems="flex-start">
        <TextField
          label={t("registration_code")}
          value={regCode}
          onChange={(e) => { setRegCode(e.target.value.toUpperCase()); setCodeInfo(null); setCodeError(null); }}
          size="small"
          inputProps={{ maxLength: 8, style: { fontFamily: "monospace", letterSpacing: 2 } }}
          placeholder="e.g. AB12CD34"
          sx={{ flex: 1 }}
        />
        <Button
          variant="outlined"
          size="small"
          disabled={regCode.length < 8 || validatingCode}
          onClick={handleValidateCode}
          sx={{ mt: 0.5 }}
        >
          {validatingCode ? <CircularProgress size={18} /> : t("validate")}
        </Button>
      </Stack>
      {codeInfo && (
        <Button variant="contained" color="success" fullWidth disabled={claimingCode} onClick={handleClaimCode}>
          {claimingCode ? <CircularProgress size={22} color="inherit" /> : `Claim Unit ${codeInfo.unit_number}`}
        </Button>
      )}
    </Stack>
  );
}

// ── Step 3 / 4: Done ──────────────────────────────────────────────────────────

function DoneStep({ role, onFinish }) {
  const { t } = useTranslation("auth");
  return (
    <Stack spacing={3} alignItems="center" py={2}>
      <Typography variant="h6" color="success.main" fontWeight={700}>{t("account_created")}</Typography>
      <Typography variant="body2" color="text.secondary" align="center">
        {role === "admin"
          ? t("done_admin_desc")
          : t("done_owner_desc")}
      </Typography>
      <Button variant="contained" size="large" onClick={onFinish}>{t("go_to_dashboard")}</Button>
    </Stack>
  );
}

// ── Invite claim step ──────────────────────────────────────────────────────────

function InviteClaimStep({ inviteToken, inviteInfo, onDone }) {
  const { t } = useTranslation("auth");
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState(null);

  const handleClaim = async () => {
    setClaiming(true);
    setError(null);
    try {
      await apartmentsApi.useInvite(inviteToken);
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || t("errors:server_error"));
    } finally {
      setClaiming(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Alert severity="success" icon={false}>
        <Typography fontWeight={600}>{t("invite_title")}</Typography>
        <Typography variant="body2">
          Claim <strong>Unit {inviteInfo.unit_number}</strong> in{" "}
          <strong>{inviteInfo.building_name}</strong> ({inviteInfo.building_city})
        </Typography>
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      <Stack direction="row" spacing={2}>
        <Button variant="outlined" fullWidth onClick={onDone}>{t("skip_for_now")}</Button>
        <Button variant="contained" fullWidth disabled={claiming} onClick={handleClaim}>
          {claiming ? <CircularProgress size={22} color="inherit" /> : t("claim_unit")}
        </Button>
      </Stack>
    </Stack>
  );
}

// ── Main wizard ────────────────────────────────────────────────────────────────

export default function RegisterPage() {
  const { t } = useTranslation("auth");
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(0);
  const [role, setRole] = useState("owner");
  const { user: existingUser } = useAuthStore();

  // If a user was already logged in before arriving at /register, redirect them away.
  // We only run this on mount ([] deps) so the check does NOT fire when AccountStep
  // calls login() mid-wizard — that would incorrectly redirect mid-flow.
  useEffect(() => {
    if (existingUser) navigate("/dashboard", { replace: true });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Invite flow state
  const inviteToken = searchParams.get("invite");
  const [inviteInfo, setInviteInfo] = useState(null);
  const [inviteError, setInviteError] = useState(null);
  const [inviteLoading, setInviteLoading] = useState(!!inviteToken);

  useEffect(() => {
    if (!inviteToken) return;
    apartmentsApi.validateInvite(inviteToken)
      .then((res) => setInviteInfo(res.data))
      .catch((err) => setInviteError(err.response?.data?.detail || "Invalid or expired invite link."))
      .finally(() => setInviteLoading(false));
  }, [inviteToken]);

  // For invited owners: Account(0) → Claim Unit(1) → Done(2)
  const STEPS_ADMIN = [t("step_account"), t("step_buildings"), t("step_unit"), t("step_done")];
  const STEPS_OWNER = [t("step_account"), t("step_unit"), t("step_done")];
  const STEPS_INVITE = [t("step_account"), t("step_claim_unit"), t("step_done")];
  const steps = inviteToken
    ? STEPS_INVITE
    : role === "admin" ? STEPS_ADMIN : STEPS_OWNER;

  if (inviteLoading) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
    <PublicSEO
      title="Get Started – ABEM"
      description="Create your ABEM account and start managing your building's expenses in minutes."
    />
    <Box display="flex" alignItems="center" justifyContent="center"
      minHeight="100vh" bgcolor="background.default" px={2} py={4} position="relative">
      <Box sx={{ position: "absolute", top: 16, right: 16 }}>
        <LanguageSwitcher />
      </Box>
      <Card sx={{ width: "100%", maxWidth: 560 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={0.5} mb={3}>
            <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 40 }} />
            <Typography variant="body2" color="text.secondary">{t("create_account")}</Typography>
          </Stack>

          {inviteToken && inviteError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {inviteError}{" "}
              <Link component={RouterLink} to="/register">{t("register_without_invite")}</Link>
            </Alert>
          ) : (
            <>
              <Stepper activeStep={step} alternativeLabel sx={{ mb: 4 }}>
                {steps.map((label) => (
                  <Step key={label}><StepLabel>{label}</StepLabel></Step>
                ))}
              </Stepper>
              <Divider sx={{ mb: 3 }} />
            </>
          )}

          {/* Invite path: Account → Claim Unit → Done */}
          {inviteToken && !inviteError && (
            <>
              {step === 0 && (
                <AccountStep
                  prefillEmail={inviteInfo?.invited_email}
                  onDone={(r) => { setRole(r); setStep(1); }}
                />
              )}
              {step === 1 && (
                <InviteClaimStep
                  inviteToken={inviteToken}
                  inviteInfo={inviteInfo}
                  onDone={() => setStep(2)}
                />
              )}
              {step === 2 && (
                <DoneStep role="owner" onFinish={() => navigate("/dashboard", { replace: true })} />
              )}
            </>
          )}

          {/* Normal path */}
          {!inviteToken && (
            <>
              {step === 0 && (
                <AccountStep
                  prefillEmail={searchParams.get("email") || ""}
                  onDone={(r) => { setRole(r); setStep(1); }}
                />
              )}

              {/* Admin path: Buildings → Unit → Done */}
              {step === 1 && role === "admin" && (
                <AdminBuildingsStep onDone={() => setStep(2)} onSkip={() => setStep(2)} />
              )}
              {step === 2 && role === "admin" && (
                <ClaimUnitStep isAdmin onDone={() => setStep(3)} onSkip={() => setStep(3)} />
              )}
              {step === 3 && role === "admin" && (
                <DoneStep role={role} onFinish={() => navigate("/dashboard", { replace: true })} />
              )}

              {/* Owner path: Unit → Done */}
              {step === 1 && role === "owner" && (
                <ClaimUnitStep onDone={() => setStep(2)} onSkip={() => setStep(2)} />
              )}
              {step === 2 && role === "owner" && (
                <DoneStep role={role} onFinish={() => navigate("/dashboard", { replace: true })} />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
    </>
  );
}
