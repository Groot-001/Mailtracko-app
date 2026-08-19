import { create } from "zustand";
import { persist } from "zustand/middleware";

export type WorkspaceTheme = "light" | "dark";

interface UiPreferencesState {
  workspaceTheme: WorkspaceTheme;
  setWorkspaceTheme: (theme: WorkspaceTheme) => void;
  resetUiPreferences: () => void;
}

const defaults: Pick<UiPreferencesState, "workspaceTheme"> = {
  workspaceTheme: "light",
};

export const useUiPreferencesStore = create<UiPreferencesState>()(
  persist(
    (set) => ({
      ...defaults,
      setWorkspaceTheme: (workspaceTheme) => set({ workspaceTheme }),
      resetUiPreferences: () => set(defaults),
    }),
    {
      name: "mailtracko-ui-preferences",
      version: 2,
      migrate: (persistedState) => {
        const state = (persistedState ?? {}) as { workspaceTheme?: string };
        return {
          workspaceTheme:
            state.workspaceTheme === "dark" || state.workspaceTheme === "midnight-focus"
              ? "dark"
              : "light",
        };
      },
    },
  ),
);
