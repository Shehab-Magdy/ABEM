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
import { authApi } from "../../api/authApi";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { useAuthStore } from "../../contexts/authStore";

const STEPS_ADMIN = ["Account", "Your Buildings", "Your Unit", "Done"];
const STEPS_OWNER = ["Account", "Your Unit", "Done"];

// ── Step 1: Account ────────────────────────────────────────────────────────────

function AccountStep({ onDone, prefillEmail }) {
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
        setError(errObj || "Registration failed.");
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
          <TextField label="First name *" fullWidth autoFocus
            error={!!errors.first_name} helperText={errors.first_name?.message}
            {...register("first_name", { required: "Required." })} />
          <TextField label="Last name *" fullWidth
            error={!!errors.last_name} helperText={errors.last_name?.message}
            {...register("last_name", { required: "Required." })} />
        </Stack>
        <TextField label="Email address *" type="email" fullWidth
          error={!!errors.email} helperText={errors.email?.message}
          {...register("email", {
            required: "Required.",
            pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Invalid email." },
          })} />
        <TextField
          label="Phone (optional)"
          type="tel"
          fullWidth
          error={!!errors.phone}
          helperText={errors.phone?.message || "Include country code, e.g. +20 1234567890"}
          {...register("phone", {
            validate: (v) => {
              if (!v || v.trim() === "") return true;
              return /^\+?[1-9][\d\s\-().]{6,19}$/.test(v.trim()) || "Enter a valid international phone number (e.g. +20 1234567890).";
            },
          })}
        />
        <TextField label="Password *" type={showPw ? "text" : "password"} fullWidth
          error={!!errors.password}
          helperText={errors.password?.message || "Min 8 chars, 1 uppercase, 1 digit, 1 special char."}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPw((p) => !p)} edge="end" tabIndex={-1}>
                  {showPw ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          {...register("password", { required: "Required." })} />
        <TextField label="Confirm password *" type={showPw ? "text" : "password"} fullWidth
          error={!!errors.confirm_password} helperText={errors.confirm_password?.message}
          {...register("confirm_password", {
            required: "Required.",
            validate: (v) => v === password || "Passwords do not match.",
          })} />
        <FormControl component="fieldset">
          <FormLabel>I am a…</FormLabel>
          <Controller
            name="role"
            control={control}
            defaultValue="owner"
            render={({ field }) => (
              <RadioGroup row {...field}>
                <FormControlLabel value="owner" control={<Radio />} label="Owner (apartment / tenant)" />
                <FormControlLabel value="admin" control={<Radio />} label="Admin (building manager)" />
              </RadioGroup>
            )}
          />
        </FormControl>
        <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
          {loading ? <CircularProgress size={24} color="inherit" /> : "Continue"}
        </Button>
        <Typography variant="body2" align="center" color="text.secondary">
          Already have an account?{" "}
          <Link component={RouterLink} to="/login" underline="hover">Sign in</Link>
        </Typography>
      </Stack>
    </Box>
  );
}

// ── Step 2 Admin: Add buildings ────────────────────────────────────────────────

function AdminBuildingsStep({ onDone, onSkip }) {
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
        setError(errObj || "Could not save buildings.");
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
          Add the buildings you manage. You can add more later from the dashboard.
        </Typography>
        {fields.map((field, idx) => (
          <Box key={field.id} sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 2 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
              <Typography variant="subtitle2" fontWeight={600}>Building {idx + 1}</Typography>
              {fields.length > 1 && (
                <IconButton size="small" color="error" onClick={() => remove(idx)}>
                  <Delete fontSize="small" />
                </IconButton>
              )}
            </Stack>
            <Stack spacing={2}>
              <TextField label="Name *" fullWidth size="small"
                error={!!errors.buildings?.[idx]?.name} helperText={errors.buildings?.[idx]?.name?.message}
                {...register(`buildings.${idx}.name`, { required: "Required." })} />
              <TextField label="Address *" fullWidth size="small"
                error={!!errors.buildings?.[idx]?.address} helperText={errors.buildings?.[idx]?.address?.message}
                {...register(`buildings.${idx}.address`, { required: "Required." })} />
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label="City *" fullWidth size="small"
                  error={!!errors.buildings?.[idx]?.city} helperText={errors.buildings?.[idx]?.city?.message}
                  {...register(`buildings.${idx}.city`, { required: "Required." })} />
                <TextField label="Country" fullWidth size="small"
                  {...register(`buildings.${idx}.country`)} />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <TextField label="Floors *" type="number" size="small" fullWidth
                  inputProps={{ min: 1 }}
                  {...register(`buildings.${idx}.num_floors`)} />
                <TextField label="# Apartments" type="number" size="small" fullWidth
                  inputProps={{ min: 0 }}
                  helperText="Auto-created as A1, A2…"
                  {...register(`buildings.${idx}.num_apartments`)} />
                <TextField label="# Stores" type="number" size="small" fullWidth
                  inputProps={{ min: 0 }}
                  helperText="Auto-created as S1, S2…"
                  {...register(`buildings.${idx}.num_stores`)} />
              </Stack>
            </Stack>
          </Box>
        ))}
        <Button variant="outlined" startIcon={<Add />} size="small" sx={{ alignSelf: "flex-start" }}
          onClick={() => append({ name: "", address: "", city: "", country: "", num_floors: 1, num_apartments: 0, num_stores: 0 })}>
          Add another building
        </Button>
        <Stack direction="row" spacing={2}>
          <Button variant="outlined" fullWidth onClick={onSkip}>Skip for now</Button>
          <Button type="submit" variant="contained" fullWidth disabled={submitting}>
            {submitting ? <CircularProgress size={22} color="inherit" /> : "Save & Continue"}
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}

// ── Shared: Select and claim a unit ───────────────────────────────────────────

function ClaimUnitStep({ onDone, onSkip, isAdmin }) {
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
      .catch(() => setError("Could not load buildings. Try again."))
      .finally(() => setLoadingBuildings(false));
  }, []);

  useEffect(() => {
    if (!selectedBuilding) { setApartments([]); return; }
    setLoadingApts(true);
    setSelectedApartment("");
    apartmentsApi.available(selectedBuilding)
      .then((r) => setApartments(r.data))
      .catch(() => setError("Could not load units."))
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
      setError(err.response?.data?.detail || "Could not claim unit.");
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
      setCodeError(err.response?.data?.detail || "Invalid or expired code.");
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
      setCodeError(err.response?.data?.detail || "Could not claim unit.");
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
          ? "If you also own a unit in one of your buildings, select it here. You can skip and do this later."
          : "Select your building and the unit you own. You can update this later from your profile."}
      </Typography>
      {buildings.length === 0 ? (
        <Alert severity="info">
          No buildings registered yet.{" "}
          {isAdmin
            ? "Go back and add your building first, or skip."
            : "Ask your building manager to register the building first."}
        </Alert>
      ) : (
        <>
          <FormControl fullWidth>
            <InputLabel>Select building</InputLabel>
            <Select
              label="Select building"
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
              <Alert severity="info">No available units in this building.</Alert>
            ) : (
              <>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">Filter by type:</Typography>
                  <ToggleButtonGroup
                    value={unitTypeFilter}
                    exclusive
                    onChange={(_, v) => { if (v) { setUnitTypeFilter(v); setSelectedApartment(""); } }}
                    size="small"
                  >
                    <ToggleButton value="all">All</ToggleButton>
                    <ToggleButton value="apartment">Apartments</ToggleButton>
                    <ToggleButton value="store">Stores</ToggleButton>
                  </ToggleButtonGroup>
                </Stack>
                {filtered.length === 0 ? (
                  <Alert severity="info">No {unitTypeFilter} units available in this building.</Alert>
                ) : (
                  <FormControl fullWidth>
                    <InputLabel>Select your unit number</InputLabel>
                    <Select
                      label="Select your unit number"
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
        <Button variant="outlined" fullWidth onClick={onSkip}>Skip for now</Button>
        <Button variant="contained" fullWidth disabled={!selectedApartment || claiming} onClick={handleClaim}>
          {claiming ? <CircularProgress size={22} color="inherit" /> : "Claim Unit"}
        </Button>
      </Stack>

      {/* Registration code alternative */}
      <Divider sx={{ my: 1 }}>
        <Typography variant="caption" color="text.secondary">or use a registration code</Typography>
      </Divider>
      {codeError && <Alert severity="error" onClose={() => setCodeError(null)}>{codeError}</Alert>}
      {codeInfo && (
        <Alert severity="success">
          Found: <strong>Unit {codeInfo.unit_number}</strong> in <strong>{codeInfo.building_name}</strong>
        </Alert>
      )}
      <Stack direction="row" spacing={1} alignItems="flex-start">
        <TextField
          label="Registration Code"
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
          {validatingCode ? <CircularProgress size={18} /> : "Validate"}
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
  return (
    <Stack spacing={3} alignItems="center" py={2}>
      <Typography variant="h6" color="success.main" fontWeight={700}>Account created!</Typography>
      <Typography variant="body2" color="text.secondary" align="center">
        {role === "admin"
          ? "Your buildings have been set up. Manage apartments, expenses, and payments from your dashboard."
          : "Your account is ready. Head to the dashboard to view your expenses and payments."}
      </Typography>
      <Button variant="contained" size="large" onClick={onFinish}>Go to Dashboard</Button>
    </Stack>
  );
}

// ── Invite claim step ──────────────────────────────────────────────────────────

function InviteClaimStep({ inviteToken, inviteInfo, onDone }) {
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState(null);

  const handleClaim = async () => {
    setClaiming(true);
    setError(null);
    try {
      await apartmentsApi.useInvite(inviteToken);
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to claim unit.");
    } finally {
      setClaiming(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Alert severity="success" icon={false}>
        <Typography fontWeight={600}>You have been invited!</Typography>
        <Typography variant="body2">
          Claim <strong>Unit {inviteInfo.unit_number}</strong> in{" "}
          <strong>{inviteInfo.building_name}</strong> ({inviteInfo.building_city})
        </Typography>
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      <Stack direction="row" spacing={2}>
        <Button variant="outlined" fullWidth onClick={onDone}>Skip for now</Button>
        <Button variant="contained" fullWidth disabled={claiming} onClick={handleClaim}>
          {claiming ? <CircularProgress size={22} color="inherit" /> : "Claim My Unit"}
        </Button>
      </Stack>
    </Stack>
  );
}

// ── Main wizard ────────────────────────────────────────────────────────────────

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(0);
  const [role, setRole] = useState("owner");

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
  const STEPS_INVITE = ["Account", "Claim Unit", "Done"];
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
    <Box display="flex" alignItems="center" justifyContent="center"
      minHeight="100vh" bgcolor="background.default" px={2} py={4}>
      <Card sx={{ width: "100%", maxWidth: 560 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={0.5} mb={3}>
            <Box component="img" src="/abem-logo-light.svg" alt="ABEM" sx={{ height: 40 }} />
            <Typography variant="body2" color="text.secondary">Create your account</Typography>
          </Stack>

          {inviteToken && inviteError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {inviteError}{" "}
              <Link component={RouterLink} to="/register">Register without invite</Link>
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
  );
}
