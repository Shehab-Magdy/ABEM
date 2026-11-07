import axiosClient from "./axiosClient";

export const authApi = {
  // ── Passwordless auth: email OTP + Google Sign-In ──────────────────────────
  // requestOtp: emails a 6-digit code, OR — if the browser already holds a
  // valid `trusted_device` cookie for this email's account — returns
  // {access, user} directly (same shape as verifyOtp) and the caller should
  // treat that as an immediate successful login, skipping the code step.
  requestOtp: (email) => axiosClient.post("/auth/otp/request/", { email }),
  verifyOtp: (email, code) => axiosClient.post("/auth/otp/verify/", { email, code }),
  googleLogin: (idToken) => axiosClient.post("/auth/google/", { id_token: idToken }),
  revokeAllDevices: () => axiosClient.post("/auth/devices/revoke-all/"),
  listSessions: () => axiosClient.get("/auth/sessions/"),
  revokeSession: (id) => axiosClient.post(`/auth/sessions/${id}/revoke/`),

  deleteAccount: (code, confirmBalance = false) =>
    axiosClient.post("/auth/delete-account/", { code, ...(confirmBalance ? { confirm_balance: true } : {}) }),
  logout: () => axiosClient.post("/auth/logout/"),
  refresh: () => axiosClient.post("/auth/refresh/"),
  selfRegister: (data) => axiosClient.post("/auth/self-register/", data),
  getProfile: () => axiosClient.get("/auth/profile/"),
  updateProfile: (data) => axiosClient.patch("/auth/profile/", data),
  uploadProfilePicture: (file) => {
    const fd = new FormData();
    fd.append("profile_picture", file);
    return axiosClient.patch("/auth/profile/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
