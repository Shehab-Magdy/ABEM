import axiosClient from "./axiosClient";

export const operationsApi = {
  contractors: (params) => axiosClient.get("/operations/contractors/", { params }),
  saveContractor: (id, data) => (id ? axiosClient.patch(`/operations/contractors/${id}/`, data) : axiosClient.post("/operations/contractors/", data)),
  deleteContractor: (id) => axiosClient.delete(`/operations/contractors/${id}/`),
  obligations: (params) => axiosClient.get("/operations/obligations/", { params }),
  saveObligation: (id, data) => (id ? axiosClient.patch(`/operations/obligations/${id}/`, data) : axiosClient.post("/operations/obligations/", data)),
  deleteObligation: (id) => axiosClient.delete(`/operations/obligations/${id}/`),
  markDone: (id) => axiosClient.post(`/operations/obligations/${id}/done/`),
};
