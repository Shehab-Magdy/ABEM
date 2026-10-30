import axiosClient from "./axiosClient";

export const expensesApi = {
  /** Large costs wait for the chair (or a resident vote): approve, reject, or put to a vote. */
  approve: (id, note) => axiosClient.post(`/expenses/${id}/approve/`, { note }),
  reject: (id, note) => axiosClient.post(`/expenses/${id}/reject/`, { note }),
  putToVote: (id) => axiosClient.post(`/expenses/${id}/put-to-vote/`, {}),
  /** Late fees added to overdue subscription shares; an admin can waive one. */
  lateFees: (params) => axiosClient.get("/expenses/late-fees/", { params }),
  waiveLateFee: (id, reason) => axiosClient.post(`/expenses/late-fees/${id}/waive/`, { reason }),
  list: (params, { signal } = {}) => axiosClient.get("/expenses/", { params, signal }),
  get: (id, { signal } = {}) => axiosClient.get(`/expenses/${id}/`, { signal }),
  create: (data) => axiosClient.post("/expenses/", data),
  update: (id, data) => axiosClient.patch(`/expenses/${id}/`, data),
  remove: (id) => axiosClient.delete(`/expenses/${id}/`),
  markPaid: (id) => axiosClient.post(`/expenses/${id}/mark_paid/`),
  uploadBill: (id, formData) =>
    axiosClient.post(`/expenses/${id}/upload/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listCategories: (buildingId, { signal } = {}) =>
    axiosClient.get("/expenses/categories/", { params: { building_id: buildingId }, signal }),
  createCategory: (data) => axiosClient.post("/expenses/categories/", data),
  removeCategory: (id) => axiosClient.delete(`/expenses/categories/${id}/`),
};
