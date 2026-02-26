import axiosClient from "./axiosClient";

export const authApi = {
  login: (credentials) => axiosClient.post("/auth/login/", credentials),
  logout: (refreshToken) => axiosClient.post("/auth/logout/", { refresh: refreshToken }),
  refresh: (refreshToken) => axiosClient.post("/auth/refresh/", { refresh: refreshToken }),
  selfRegister: (data) => axiosClient.post("/auth/self-register/", data),
  changePassword: (data) => axiosClient.patch("/auth/change-password/", data),
  getProfile: () => axiosClient.get("/auth/profile/"),
  updateProfile: (data) => axiosClient.patch("/auth/profile/", data),
};
