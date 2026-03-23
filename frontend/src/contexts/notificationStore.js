import { create } from "zustand";

export const useNotificationStore = create((set) => ({
  unreadCount: 0,
  setUnreadCount: (count) => set({ unreadCount: count }),
  decrementUnread: () =>
    set((state) => ({ unreadCount: Math.max(0, state.unreadCount - 1) })),
  clearUnread: () => set({ unreadCount: 0 }),
}));
