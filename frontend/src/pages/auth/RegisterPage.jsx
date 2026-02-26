/**
 * Multi-step registration wizard.
 *
 * Step 1 (all):   Account details + role selection (Admin | Owner)
 * Step 2 Admin:   Add one or more buildings to manage (can skip)
 * Step 2 Owner:   Select a building → select an available apartment to claim (can skip)
 * Step 3:         Success — redirect to dashboard
 */
import { useEffect, useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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
  Typography,
} from "@mui/material";
import { Add, Delete, Visibility, VisibilityOff } from "@mui/icons-material";
import { authApi } from "../../api/authApi";
import { buildingsApi } from "../../api/buildingsApi";
import { apartmentsApi } from "../../api/apartmentsApi";
import { useAuthStore } from "../../contexts/authStore";

const STEPS_ADMIN = ["Account", "Your Buildings", "Done"];
const STEPS_OWNER = ["Account", "Your Apartment", "Done"];

// ── Step 1: Account ────────────────────────────────────────────────────────────

function AccountStep({ onDone }) {
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { login } = useAuthStore();
  const { register, handleSubmit, watch, control, formState: { errors } } = useForm({ defaultValues: { role: "owner" } });
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
        <TextField label="Phone (optional)" type="tel" fullWidth {...register("phone")} />
        <TextField label="Password *" type={showPw ? "text" : "password"} fullWidth
          error={!!errors.password}
          helperText={errors.password?.message || "Min 8 chars, 1 uppercase, 1 digit, 1 special char."}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPw((p) => !p)} edge="end">
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
    defaultValues: { buildings: [{ name: "", address: "", city: "", country: "", num_floors: 1 }] },
  });
  const { fields, append, remove } = useFieldArray({ control, name: "buildings" });

  const onSubmit = async (data) => {
    setError(null);
    setSubmitting(true);
    try {
      for (const b of data.buildings) {
        if (b.name.trim()) {
          await buildingsApi.create({
            name: b.name, address: b.address, city: b.city,
            country: b.country || "", num_floors: parseInt(b.num_floors, 10) || 1,
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
              <TextField label="Number of floors *" type="number" size="small"
                inputProps={{ min: 1 }} sx={{ maxWidth: 200 }}
                {...register(`buildings.${idx}.num_floors`)} />
            </Stack>
          </Box>
        ))}
        <Button variant="outlined" startIcon={<Add />} size="small" sx={{ alignSelf: "flex-start" }}
          onClick={() => append({ name: "", address: "", city: "", country: "", num_floors: 1 })}>
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

// ── Step 2 Owner: Select building + apartment ──────────────────────────────────

function OwnerApartmentStep({ onDone, onSkip }) {
  const [buildings, setBuildings] = useState([]);
  const [apartments, setApartments] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState("");
  const [selectedApartment, setSelectedApartment] = useState("");
  const [loadingBuildings, setLoadingBuildings] = useState(true);
  const [loadingApts, setLoadingApts] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState(null);

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
      .catch(() => setError("Could not load apartments."))
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
      setError(err.response?.data?.detail || "Could not claim apartment.");
    } finally {
      setClaiming(false);
    }
  };

  if (loadingBuildings) return <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>;

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error" onClose={() => setError(null)}>{error}</Alert>}
      <Typography variant="body2" color="text.secondary">
        Select your building and the apartment you own. You can update this later from your profile.
      </Typography>
      {buildings.length === 0 ? (
        <Alert severity="info">
          No buildings registered yet. Ask your building manager to add your building first, then you can link your apartment from the dashboard.
        </Alert>
      ) : (
        <>
          <FormControl fullWidth>
            <InputLabel>Select your building</InputLabel>
            <Select label="Select your building" value={selectedBuilding}
              onChange={(e) => setSelectedBuilding(e.target.value)}>
              {buildings.map((b) => (
                <MenuItem key={b.id} value={b.id}>{b.name} — {b.city}</MenuItem>
              ))}
            </Select>
          </FormControl>
          {selectedBuilding && (
            loadingApts ? (
              <Box display="flex" justifyContent="center"><CircularProgress size={28} /></Box>
            ) : apartments.length === 0 ? (
              <Alert severity="info">
                No available (unassigned) apartments in this building. Ask your manager to add your unit.
              </Alert>
            ) : (
              <FormControl fullWidth>
                <InputLabel>Select your apartment</InputLabel>
                <Select label="Select your apartment" value={selectedApartment}
                  onChange={(e) => setSelectedApartment(e.target.value)}>
                  {apartments.map((a) => (
                    <MenuItem key={a.id} value={a.id}>
                      Unit {a.unit_number} — Floor {a.floor}
                      {a.size_sqm ? ` — ${a.size_sqm} m²` : ""}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )
          )}
        </>
      )}
      <Stack direction="row" spacing={2}>
        <Button variant="outlined" fullWidth onClick={onSkip}>Skip for now</Button>
        <Button variant="contained" fullWidth disabled={!selectedApartment || claiming} onClick={handleClaim}>
          {claiming ? <CircularProgress size={22} color="inherit" /> : "Claim Apartment"}
        </Button>
      </Stack>
    </Stack>
  );
}

// ── Step 3: Done ───────────────────────────────────────────────────────────────

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

// ── Main wizard ────────────────────────────────────────────────────────────────

export default function RegisterPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [role, setRole] = useState("owner");

  const steps = role === "admin" ? STEPS_ADMIN : STEPS_OWNER;

  return (
    <Box display="flex" alignItems="center" justifyContent="center"
      minHeight="100vh" bgcolor="background.default" px={2} py={4}>
      <Card sx={{ width: "100%", maxWidth: 560 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack alignItems="center" spacing={0.5} mb={3}>
            <Typography variant="h4" color="primary" fontWeight={700}>ABEM</Typography>
            <Typography variant="body2" color="text.secondary">Create your account</Typography>
          </Stack>
          <Stepper activeStep={step} alternativeLabel sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}><StepLabel>{label}</StepLabel></Step>
            ))}
          </Stepper>
          <Divider sx={{ mb: 3 }} />

          {step === 0 && (
            <AccountStep onDone={(r) => { setRole(r); setStep(1); }} />
          )}
          {step === 1 && role === "admin" && (
            <AdminBuildingsStep onDone={() => setStep(2)} onSkip={() => setStep(2)} />
          )}
          {step === 1 && role === "owner" && (
            <OwnerApartmentStep onDone={() => setStep(2)} onSkip={() => setStep(2)} />
          )}
          {step === 2 && (
            <DoneStep role={role} onFinish={() => navigate("/dashboard", { replace: true })} />
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
