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
  /** Annual report (التقرير السنوي) for the general assembly. year = 2026. */
  annualReport: (id, year) => axiosClient.get(`/buildings/${id}/annual-report/`, { params: { year } }),
  annualReportPdf: (id, year) =>
    axiosClient.get(`/buildings/${id}/annual-report/`, {
      params: { year, file_format: "pdf" },
      responseType: "blob",
      timeout: 90000,
    }),
  /** Primary admin hands the building to one of its co-admins. */
  transferAdmin: (id, userId) => axiosClient.post(`/buildings/${id}/transfer-admin/`, { user_id: userId }),
  /** Monthly subscription plan (الاشتراك الشهري): amount, billing day, days until due. */
  subscription: (id) => axiosClient.get(`/buildings/${id}/subscription/`),
  saveSubscription: (id, data) => axiosClient.post(`/buildings/${id}/subscription/`, data),
  /** Board titles (chair / treasurer / secretary): everyone reads, building admins assign. */
  board: (id) => axiosClient.get(`/buildings/${id}/board/`),
  setBoardRole: (id, userId, role) => axiosClient.post(`/buildings/${id}/board/`, { user_id: userId, role }),
  /** Bulk-create units from a CSV; commit=false only checks the file. */
  importUnits: (id, file, commit) => {
    const form = new FormData();
    form.append("file", file);
    form.append("commit", commit ? "true" : "false");
    return axiosClient.post(`/buildings/${id}/import-units/`, form, multipartConfig);
  },
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
