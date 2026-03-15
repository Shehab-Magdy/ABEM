import axiosClient from "./axiosClient";

export const apartmentsApi = {
  list: (params) => axiosClient.get("/apartments/", { params }),
  get: (id) => axiosClient.get(`/apartments/${id}/`),
  create: (data) => axiosClient.post("/apartments/", data),
  update: (id, data) => axiosClient.patch(`/apartments/${id}/`, data),
  remove: (id) => axiosClient.delete(`/apartments/${id}/`),
  balance: (id) => axiosClient.get(`/apartments/${id}/balance/`),
  /** Returns all active buildings — used in sign-up wizard. */
  buildingDirectory: () => axiosClient.get("/buildings/directory/"),
  /** Returns unowned apartments for a building — used in sign-up wizard. */
  available: (buildingId) =>
    axiosClient.get("/apartments/available/", { params: { building_id: buildingId } }),
  /** Owner claims a vacant apartment during sign-up. */
  claim: (apartmentId) => axiosClient.post(`/apartments/${apartmentId}/claim/`),
  /** Admin creates an invite token for a unit. */
  inviteUnit: (unitId, email) => axiosClient.post(`/apartments/${unitId}/invite/`, { email }),
  /** Validate an invite token or registration code (public — no auth required). */
  validateInvite: (token, code) => axiosClient.get("/apartments/invite/validate/", { params: { token, code } }),
  /** Authenticated user redeems an invite token to claim their unit. */
  useInvite: (token) => axiosClient.post("/apartments/invite/use/", { token }),
  /** Authenticated user redeems a registration code to claim their unit. */
  useInviteCode: (code) => axiosClient.post("/apartments/invite/use/", { code }),
};
