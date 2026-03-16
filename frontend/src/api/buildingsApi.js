import axiosClient from "./axiosClient";

export const buildingsApi = {
  list: (params) => axiosClient.get("/buildings/", { params }),
  get: (id) => axiosClient.get(`/buildings/${id}/`),
  create: (data) => axiosClient.post("/buildings/", data),
  update: (id, data) => axiosClient.patch(`/buildings/${id}/`, data),
  remove: (id) => axiosClient.delete(`/buildings/${id}/`),
  assignUser: (id, userId) =>
    axiosClient.post(`/buildings/${id}/assign-user/`, { user_id: userId }),
  apartments: (id) => axiosClient.get(`/buildings/${id}/apartments/`),
  deactivate: (id) => axiosClient.post(`/buildings/${id}/deactivate/`),
  activate: (id) => axiosClient.post(`/buildings/${id}/activate/`),
};
