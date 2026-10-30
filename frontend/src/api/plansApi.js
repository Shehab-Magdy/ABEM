import axiosClient from "./axiosClient";

export const plansApi = {
  tiers: () => axiosClient.get("/plans/tiers/"),
  saveTier: (code, data) => (code ? axiosClient.patch(`/plans/tiers/${code}/`, data) : axiosClient.post("/plans/tiers/", data)),
  current: (buildingId) => axiosClient.get("/plans/current/", { params: { building_id: buildingId } }),
  payments: () => axiosClient.get("/plans/payments/"),
  pay: (data) => axiosClient.post("/plans/payments/", data),
  confirm: (id) => axiosClient.post(`/plans/payments/${id}/confirm/`),
  reject: (id) => axiosClient.post(`/plans/payments/${id}/reject/`),
  settings: () => axiosClient.get("/plans/settings/"),
  saveSettings: (data) => axiosClient.patch("/plans/settings/", data),
};
