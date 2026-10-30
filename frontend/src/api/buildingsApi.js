import axiosClient from "./axiosClient";

const multipartConfig = { headers: { "Content-Type": "multipart/form-data" } };

export const buildingsApi = {
  /** Current balance (خزينة العمارة) — read-only, visible to admins and residents. */
  treasury: (id) => axiosClient.get(`/buildings/${id}/treasury/`),
  /** Monthly statement (كشف حساب شهري). month = "YYYY-MM". */
  statement: (id, month) => axiosClient.get(`/buildings/${id}/statement/`, { params: { month } }),
  statementPdf: (id, month) =>
    axiosClient.get(`/buildings/${id}/statement/`, {
      params: { month, file_format: "pdf" },
      responseType: "blob",
      timeout: 90000,
    }),
  /** Primary admin hands the building to one of its co-admins. */
  transferAdmin: (id, userId) => axiosClient.post(`/buildings/${id}/transfer-admin/`, { user_id: userId }),
  list: (params, { signal } = {}) => axiosClient.get("/buildings/", { params, signal }),
  get: (id, { signal } = {}) => axiosClient.get(`/buildings/${id}/`, { signal }),
  create: (data) => axiosClient.post("/buildings/", data, data instanceof FormData ? multipartConfig : undefined),
  update: (id, data) => axiosClient.patch(`/buildings/${id}/`, data, data instanceof FormData ? multipartConfig : undefined),
  remove: (id) => axiosClient.delete(`/buildings/${id}/`),
  assignUser: (id, userId) =>
    axiosClient.post(`/buildings/${id}/assign-user/`, { user_id: userId }),
  apartments: (id, params, { signal } = {}) => axiosClient.get(`/buildings/${id}/apartments/`, { params, signal }),
  deactivate: (id) => axiosClient.post(`/buildings/${id}/deactivate/`),
  activate: (id) => axiosClient.post(`/buildings/${id}/activate/`),
};
