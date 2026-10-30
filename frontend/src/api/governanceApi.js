import axiosClient from "./axiosClient";

export const governanceApi = {
  /** Minutes (محاضر) and documents of a building: members read; the secretary and admins write. */
  meetings: (params) => axiosClient.get("/governance/meetings/", { params }),
  saveMeeting: (id, data) => (id ? axiosClient.patch(`/governance/meetings/${id}/`, data) : axiosClient.post("/governance/meetings/", data)),
  deleteMeeting: (id) => axiosClient.delete(`/governance/meetings/${id}/`),
  meetingPdf: (id) => axiosClient.get(`/governance/meetings/${id}/pdf/`, { responseType: "blob", timeout: 90000 }),
  documents: (params) => axiosClient.get("/governance/documents/", { params }),
  uploadDocument: (form) => axiosClient.post("/governance/documents/", form, { headers: { "Content-Type": "multipart/form-data" } }),
  deleteDocument: (id) => axiosClient.delete(`/governance/documents/${id}/`),
  polls: (params) => axiosClient.get("/governance/polls/", { params }),
  createPoll: (data) => axiosClient.post("/governance/polls/", data),
  vote: (pollId, apartmentId, optionId) =>
    axiosClient.post(`/governance/polls/${pollId}/vote/`, { apartment_id: apartmentId, option_id: optionId }),
  closePoll: (pollId) => axiosClient.post(`/governance/polls/${pollId}/close/`),
};
