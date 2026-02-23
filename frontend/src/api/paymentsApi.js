import axiosClient from "./axiosClient";

export const paymentsApi = {
  list: (params) => axiosClient.get("/payments/", { params }),
  get: (id) => axiosClient.get(`/payments/${id}/`),
  create: (data) => axiosClient.post("/payments/", data),
  getApartmentBalance: (apartmentId) =>
    axiosClient.get(`/apartments/${apartmentId}/balance/`),
};
