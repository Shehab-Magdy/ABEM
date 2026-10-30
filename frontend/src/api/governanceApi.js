import axiosClient from "./axiosClient";

export const governanceApi = {
  polls: (params) => axiosClient.get("/governance/polls/", { params }),
  createPoll: (data) => axiosClient.post("/governance/polls/", data),
  vote: (pollId, apartmentId, optionId) =>
    axiosClient.post(`/governance/polls/${pollId}/vote/`, { apartment_id: apartmentId, option_id: optionId }),
  closePoll: (pollId) => axiosClient.post(`/governance/polls/${pollId}/close/`),
};
