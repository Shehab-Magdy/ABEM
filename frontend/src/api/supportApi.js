import axiosClient from "./axiosClient";

export const supportApi = {
  /** Send a problem report; screenshot is an optional image File. */
  report: ({ message, page, screenshot }) => {
    const form = new FormData();
    form.append("message", message);
    if (page) form.append("page", page);
    if (screenshot) form.append("screenshot", screenshot);
    return axiosClient.post("/support/tickets/", form, { headers: { "Content-Type": "multipart/form-data" } });
  },
};
