import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Loader2, Moon, Palette, Save, Sun } from "lucide-react";

import { editOrganization, getOrganization } from "../../../../feature/organization/api/organizationApi";
import { getPlatformAccess } from "../../../../feature/platform/api/platformApi";
import { updateProfile } from "../../../../shared/api/authApi";
import { useAuthStore } from "../../../../shared/store/AuthStore";
import {
  useUiPreferencesStore,
  type WorkspaceTheme,
} from "../../../../shared/store/UiPreferencesStore";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";

export const Route = createFileRoute("/_protected/organization/account-settings/preferences")({
  component: AppearanceSettings,
});

const THEMES: Array<{
  id: WorkspaceTheme;
  name: string;
  description: string;
  icon: typeof Sun;
}> = [
  { id: "light", name: "Light", description: "Bright, clean surfaces for everyday work.", icon: Sun },
  { id: "dark", name: "Dark", description: "Low-light surfaces for focused work.", icon: Moon },
];

function AppearanceSettings() {
  const queryClient = useQueryClient();
  const organization = useQuery({ queryKey: ["organization", "current"], queryFn: getOrganization });
  const access = useQuery({ queryKey: ["platform", "access"], queryFn: getPlatformAccess });
  const storedTheme = useUiPreferencesStore((state) => state.workspaceTheme);
  const setWorkspaceTheme = useUiPreferencesStore((state) => state.setWorkspaceTheme);
  const setUser = useAuthStore((state) => state.setUser);

  const serverTheme = useMemo<WorkspaceTheme>(() => {
    return organization.data?.theme === "dark" ? "dark" : organization.data?.theme === "light" ? "light" : storedTheme;
  }, [organization.data?.theme, storedTheme]);

  const [theme, setTheme] = useState<WorkspaceTheme>(serverTheme);
  const [saved, setSaved] = useState(false);

  useEffect(() => setTheme(serverTheme), [serverTheme]);

  const canManageWorkspaceAppearance =
    access.data?.workspace_role === "owner" || Boolean(access.data?.workspace_permissions?.manage_organization);

  const save = useMutation({
    mutationFn: async () => {
      const org = organization.data;
      if (org && theme !== serverTheme) {
        if (!canManageWorkspaceAppearance) {
          throw new Error("Only a workspace owner or an authorized admin can change the workspace theme.");
        }
        await editOrganization(org.uuid, { theme });
      }

      setWorkspaceTheme(theme);
      const updatedUser = await updateProfile({ theme });
      setUser(updatedUser);
    },
    onSuccess: async () => {
      setSaved(true);
      await queryClient.invalidateQueries({ queryKey: ["organization", "current"] });
      window.setTimeout(() => setSaved(false), 2500);
    },
  });

  if (organization.isLoading || access.isLoading) {
    return <div className="grid min-h-48 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2"><Palette className="h-5 w-5 text-[#8F740D]" /><h2 className="text-xl font-bold text-[#1A1C1C]">Appearance</h2></div>
        <p className="mt-1 text-sm text-[#756F60]">Choose the same Light or Dark theme supported throughout MailTracko.</p>
      </div>

      <section className="rounded-2xl border border-[#E8DFC5] bg-white p-5">
        <h3 className="text-sm font-bold text-[#1A1C1C]">Workspace theme</h3>
        <p className="mt-1 text-xs text-[#756F60]">Theme changes persist on the workspace and your account.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {THEMES.map((item) => {
            const selected = theme === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setTheme(item.id)}
                className={`relative rounded-xl border p-4 text-left transition ${selected ? "border-[#8F740D] bg-[#FFFBEE] ring-1 ring-[#8F740D]/20" : "border-[#E8DFC5] hover:border-[#C6AC42]"}`}
              >
                {selected && <Check className="absolute right-3 top-3 h-4 w-4 text-[#8F740D]" />}
                <span className="mb-3 grid h-9 w-9 place-items-center rounded-lg bg-[#F5E29F]/40 text-[#8F740D]"><Icon className="h-4 w-4" /></span>
                <p className="pr-6 text-sm font-bold text-[#1A1C1C]">{item.name}</p>
                <p className="mt-1 text-xs leading-5 text-[#756F60]">{item.description}</p>
              </button>
            );
          })}
        </div>
      </section>

      {save.isError && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{getApiErrorMessage(save.error, "Appearance settings could not be saved.")}</p>}
      {saved && <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">Appearance settings saved.</p>}

      <div className="flex justify-end">
        <button type="button" disabled={save.isPending} onClick={() => save.mutate()} className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60">
          {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save appearance
        </button>
      </div>
    </div>
  );
}
