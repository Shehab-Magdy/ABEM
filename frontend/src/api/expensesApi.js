import axiosClient from "./axiosClient";

export const expensesApi = {
  list: (params) => axiosClient.get("/expenses/", { params }),
  get: (id) => axiosClient.get(`/expenses/${id}/`),
  create: (data) => axiosClient.post("/expenses/", data),
  update: (id, data) => axiosClient.patch(`/expenses/${id}/`, data),
  remove: (id) => axiosClient.delete(`/expenses/${id}/`),
  markPaid: (id) => axiosClient.post(`/expenses/${id}/mark_paid/`),
  uploadBill: (id, formData) =>
    axiosClient.post(`/expenses/${id}/upload/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listCategories: (buildingId) =>
    axiosClient.get("/expenses/categories/", { params: { building_id: buildingId } }),
  createCategory: (data) => axiosClient.post("/expenses/categories/", data),
  removeCategory: (id) => axiosClient.delete(`/expenses/categories/${id}/`),
};
