import axiosClient from "./axiosClient";

export const analyticsApi = {
  /** Usage numbers across all buildings — platform owners (superusers) only. */
  platform: () => axiosClient.get("/analytics/platform/"),
};
