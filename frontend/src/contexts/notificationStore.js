import { create } from "zustand";
import axiosClient from "../api/axiosClient";

let countRequest = null;

export const useNotificationStore = create((set) => ({
  unreadCount: 0,
  setUnreadCount: (count) => set({ unreadCount: count }),
  decrementUnread: () =>
    set((state) => ({ unreadCount: Math.max(0, state.unreadCount - 1) })),
  clearUnread: () => set({ unreadCount: 0 }),
  /** Reconcile with the server (cheap COUNT endpoint). Concurrent calls share one request. */
  refreshUnread: () => {
    if (!countRequest) {
      countRequest = axiosClient
        .get("/notifications/unread-count/")
        .then((r) => {
          if (typeof r.data?.count === "number") set({ unreadCount: r.data.count });
        })
        .catch(() => {})
        .finally(() => {
          countRequest = null;
        });
    }
    return countRequest;
  },
}));
