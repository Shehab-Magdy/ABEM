import axiosClient from "./axiosClient";

export const assetsApi = {
  list: (params) => axiosClient.get("/payments/assets/", { params }),
  create: (data) => axiosClient.post("/payments/assets/", data),
  update: (id, data) => axiosClient.patch(`/payments/assets/${id}/`, data),
  sell: (id, data) => axiosClient.post(`/payments/assets/${id}/sell/`, data),
};
