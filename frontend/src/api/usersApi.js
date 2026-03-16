import axiosClient from "./axiosClient";

export const usersApi = {
  list: (params) => axiosClient.get("/users/", { params }),
  get: (id) => axiosClient.get(`/users/${id}/`),
  create: (data) => axiosClient.post("/users/", data),
  update: (id, data) => axiosClient.patch(`/users/${id}/`, data),
  remove: (id) => axiosClient.delete(`/users/${id}/`),
  deactivate: (id) => axiosClient.post(`/users/${id}/deactivate/`),
  activate: (id) => axiosClient.post(`/users/${id}/activate/`),
  resetPassword: (id, data) => axiosClient.post(`/users/${id}/reset-password/`, data),
  setMessagingBlock: (id, data) => axiosClient.post(`/users/${id}/set-messaging-block/`, data),
};
