import axiosClient from "./axiosClient";

export const paymentsApi = {
  list: (params, { signal } = {}) => axiosClient.get("/payments/", { params, signal }),
  get: (id, { signal } = {}) => axiosClient.get(`/payments/${id}/`, { signal }),
  create: (data) => axiosClient.post("/payments/", data),
  reverse: (id, reason) => axiosClient.post(`/payments/${id}/reverse/`, { reason }),
  getApartmentBalance: (apartmentId, { signal } = {}) =>
    axiosClient.get(`/apartments/${apartmentId}/balance/`, { signal }),
  /** InstaPay display-and-confirm: residents report a transfer, admins confirm it. */
  claims: (params) => axiosClient.get("/payments/claims/", { params }),
  createClaim: (data) => axiosClient.post("/payments/claims/", data),
  confirmClaim: (id) => axiosClient.post(`/payments/claims/${id}/confirm/`),
  rejectClaim: (id) => axiosClient.post(`/payments/claims/${id}/reject/`),
  receipt: (id) =>
    axiosClient.get(`/payments/${id}/receipt/`, {
      responseType: "blob",
      timeout: 90000,
      _skipGlobalError: true,
    }),
};
