import axiosClient from "./axiosClient";

export const buildingsApi = {
  list: (params, { signal } = {}) => axiosClient.get("/buildings/", { params, signal }),
  get: (id, { signal } = {}) => axiosClient.get(`/buildings/${id}/`, { signal }),
  create: (data) => axiosClient.post("/buildings/", data),
  update: (id, data) => axiosClient.patch(`/buildings/${id}/`, data),
  remove: (id) => axiosClient.delete(`/buildings/${id}/`),
  assignUser: (id, userId) =>
    axiosClient.post(`/buildings/${id}/assign-user/`, { user_id: userId }),
  apartments: (id, params, { signal } = {}) => axiosClient.get(`/buildings/${id}/apartments/`, { params, signal }),
  deactivate: (id) => axiosClient.post(`/buildings/${id}/deactivate/`),
  activate: (id) => axiosClient.post(`/buildings/${id}/activate/`),
};
