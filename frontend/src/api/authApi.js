import axiosClient from "./axiosClient";

export const authApi = {
  login: (credentials) => axiosClient.post("/auth/login/", credentials),
  logout: (refreshToken) => axiosClient.post("/auth/logout/", { refresh: refreshToken }),
  refresh: (refreshToken) => axiosClient.post("/auth/refresh/", { refresh: refreshToken }),
  selfRegister: (data) => axiosClient.post("/auth/self-register/", data),
  changePassword: (data) => axiosClient.patch("/auth/change-password/", data),
  forceChangePassword: (data) => axiosClient.post("/auth/force-change-password/", data),
  getProfile: () => axiosClient.get("/auth/profile/"),
  updateProfile: (data) => axiosClient.patch("/auth/profile/", data),
  uploadProfilePicture: (file) => {
    const fd = new FormData();
    fd.append("profile_picture", file);
    return axiosClient.patch("/auth/profile/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
