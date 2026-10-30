import axiosClient from "./axiosClient";

export const maintenanceApi = {
  /** Work orders: a report taken on by a contractor, with its cost linked once it is recorded as an expense. */
  createWorkOrder: (data) => axiosClient.post("/maintenance/work-orders/", data),
  updateWorkOrder: (id, data) => axiosClient.patch(`/maintenance/work-orders/${id}/`, data),
  list: (params) => axiosClient.get("/maintenance/", { params }),
  create: (data) => axiosClient.post("/maintenance/", data),
  setStatus: (id, status) => axiosClient.patch(`/maintenance/${id}/`, { status }),
};
