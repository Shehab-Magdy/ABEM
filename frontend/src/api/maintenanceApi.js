import axiosClient from "./axiosClient";

export const maintenanceApi = {
  list: (params) => axiosClient.get("/maintenance/", { params }),
  create: (data) => axiosClient.post("/maintenance/", data),
  setStatus: (id, status) => axiosClient.patch(`/maintenance/${id}/`, { status }),
};
