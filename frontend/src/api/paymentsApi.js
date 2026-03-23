import axiosClient from "./axiosClient";

export const paymentsApi = {
  list: (params, { signal } = {}) => axiosClient.get("/payments/", { params, signal }),
  get: (id, { signal } = {}) => axiosClient.get(`/payments/${id}/`, { signal }),
  create: (data) => axiosClient.post("/payments/", data),
  getApartmentBalance: (apartmentId, { signal } = {}) =>
    axiosClient.get(`/apartments/${apartmentId}/balance/`, { signal }),
  receipt: (id) =>
    axiosClient.get(`/payments/${id}/receipt/`, {
      responseType: "blob",
      timeout: 90000,
      _skipGlobalError: true,
    }),
};
