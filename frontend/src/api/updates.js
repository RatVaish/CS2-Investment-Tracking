import apiClient from "./client";

export const getUnreadUpdates = async () => {
  const response = await apiClient.get("/updates/unread");
  return response.data;
};

export const markUpdatesRead = async (updateIds) => {
  const response = await apiClient.post("/updates/mark-read", updateIds);
  return response.data;
};
