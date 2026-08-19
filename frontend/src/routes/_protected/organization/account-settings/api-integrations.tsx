import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Copy, KeyRound, Loader2, Plus, Trash2, Webhook } from "lucide-react";

import {
  createApiKey,
  createWebhook,
  deleteWebhook,
  getApiKeys,
  getWebhooks,
  revokeApiKey,
} from "../../../../feature/platform/api/platformApi";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";
import { useToast } from "../../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";

export const Route = createFileRoute("/_protected/organization/account-settings/api-integrations")({ component: ApiIntegrations });

type PendingDelete =
  | { type: "key"; uuid: string; name: string }
  | { type: "webhook"; uuid: string; name: string };

function ApiIntegrations() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const keys = useQuery({ queryKey: ["platform", "api-keys"], queryFn: getApiKeys });
  const webhooks = useQuery({ queryKey: ["platform", "webhooks"], queryFn: getWebhooks });
  const [keyName, setKeyName] = useState("");
  const [webhookName, setWebhookName] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [revealed, setRevealed] = useState<{ type: "key" | "webhook"; value: string } | null>(null);
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null);

  const createKeyMutation = useMutation({
    mutationFn: createApiKey,
    onSuccess: (item) => {
      setKeyName("");
      setRevealed({ type: "key", value: item.key });
      showToast("API key created successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["platform", "api-keys"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "API key could not be created."), "error"),
  });
  const revokeKeyMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      setPendingDelete(null);
      showToast("API key revoked successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["platform", "api-keys"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "API key could not be revoked."), "error"),
  });
  const createWebhookMutation = useMutation({
    mutationFn: createWebhook,
    onSuccess: (item) => {
      setWebhookName("");
      setWebhookUrl("");
      setRevealed({ type: "webhook", value: item.secret });
      showToast("Webhook endpoint created successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["platform", "webhooks"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "Webhook endpoint could not be created."), "error"),
  });
  const deleteWebhookMutation = useMutation({
    mutationFn: deleteWebhook,
    onSuccess: () => {
      setPendingDelete(null);
      showToast("Webhook endpoint deleted successfully.", "success");
      queryClient.invalidateQueries({ queryKey: ["platform", "webhooks"] });
    },
    onError: (error) => showToast(getApiErrorMessage(error, "Webhook endpoint could not be deleted."), "error"),
  });

  const submitKey = (event: FormEvent) => {
    event.preventDefault();
    createKeyMutation.mutate({ name: keyName.trim(), scopes: ["contacts:read", "campaigns:read", "campaigns:write"] });
  };
  const submitWebhook = (event: FormEvent) => {
    event.preventDefault();
    createWebhookMutation.mutate({ name: webhookName.trim(), url: webhookUrl.trim(), events: ["campaign.completed", "recipient.replied", "recipient.bounced"] });
  };
  const copy = () => revealed && navigator.clipboard.writeText(revealed.value);
  const deleting = revokeKeyMutation.isPending || deleteWebhookMutation.isPending;

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    if (pendingDelete.type === "key") await revokeKeyMutation.mutateAsync(pendingDelete.uuid);
    else await deleteWebhookMutation.mutateAsync(pendingDelete.uuid);
  };

  return (
    <div className="space-y-6">
      
      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) setPendingDelete(null);
        }}
        title={pendingDelete?.type === "key" ? "Revoke API key?" : "Delete webhook endpoint?"}
        description={pendingDelete?.type === "key"
          ? `Revoke ${pendingDelete?.name ?? "this API key"}? Applications using it will immediately lose access.`
          : `Delete ${pendingDelete?.name ?? "this webhook"}? Event deliveries to this endpoint will stop.`}
        confirmLabel={pendingDelete?.type === "key" ? "Revoke key" : "Delete endpoint"}
        isLoading={deleting}
        onConfirm={confirmDelete}
      />

      {revealed && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-5">
          <p className="text-sm font-bold text-amber-950">Copy this {revealed.type === "key" ? "API key" : "webhook signing secret"} now</p>
          <p className="mt-1 text-xs text-amber-800">It is stored securely and cannot be displayed again.</p>
          <div className="mt-3 flex gap-2">
            <code className="min-w-0 flex-1 overflow-x-auto rounded-lg bg-white px-3 py-2 text-xs">{revealed.value}</code>
            <button type="button" onClick={copy} className="rounded-lg bg-amber-900 px-3 text-white" aria-label="Copy secret"><Copy className="h-4 w-4" /></button>
          </div>
        </div>
      )}

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div className="flex gap-3"><KeyRound className="h-5 w-5 text-[#8F740D]" /><div><h2 className="font-bold">API keys</h2><p className="text-xs text-[#756F60]">Use scoped credentials for server-to-server integrations.</p></div></div>
        <form onSubmit={submitKey} className="mt-5 flex flex-col gap-2 sm:flex-row">
          <input required maxLength={50} value={keyName} onChange={(event) => setKeyName(event.target.value)} placeholder="Key name, e.g. CRM production" className="flex-1 rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm" />
          <button disabled={createKeyMutation.isPending} className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50"><Plus className="h-4 w-4" /> {createKeyMutation.isPending ? "Creating…" : "Create key"}</button>
        </form>
        <div className="mt-5 divide-y divide-[#F4F1E8]">
          {keys.isLoading ? <Loader2 className="my-6 h-5 w-5 animate-spin" /> : keys.data?.items.map((item) => (
            <div key={item.uuid} className="flex items-center justify-between gap-4 py-4">
              <div className="min-w-0"><p className="truncate text-sm font-semibold" title={item.name}>{item.name}</p><p className="mt-1 truncate font-mono text-xs text-[#756F60]">{item.key_prefix}•••• · {item.scopes.join(", ")}</p></div>
              <button type="button" disabled={Boolean(item.revoked_at) || deleting} onClick={() => setPendingDelete({ type: "key", uuid: item.uuid, name: item.name })} className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-red-700 disabled:text-[#9A9487]"><Trash2 className="h-3.5 w-3.5" /> {item.revoked_at ? "Revoked" : "Revoke"}</button>
            </div>
          ))}
          {!keys.isLoading && !keys.data?.items.length && <p className="py-6 text-center text-sm text-[#756F60]">No API keys created.</p>}
        </div>
      </section>

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div className="flex gap-3"><Webhook className="h-5 w-5 text-[#8F740D]" /><div><h2 className="font-bold">Webhooks</h2><p className="text-xs text-[#756F60]">Receive signed lifecycle and engagement events.</p></div></div>
        <form onSubmit={submitWebhook} className="mt-5 grid gap-2 sm:grid-cols-[1fr_2fr_auto]">
          <input required maxLength={50} value={webhookName} onChange={(event) => setWebhookName(event.target.value)} placeholder="Endpoint name" className="rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm" />
          <input required type="url" value={webhookUrl} onChange={(event) => setWebhookUrl(event.target.value)} placeholder="https://your-service.com/webhooks/mailtracko" className="rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm" />
          <button disabled={createWebhookMutation.isPending} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50">{createWebhookMutation.isPending ? "Adding…" : "Add endpoint"}</button>
        </form>
        <div className="mt-5 divide-y divide-[#F4F1E8]">
          {webhooks.isLoading ? <Loader2 className="my-6 h-5 w-5 animate-spin" /> : webhooks.data?.items.map((item) => (
            <div key={item.uuid} className="flex items-start justify-between gap-4 py-4">
              <div className="min-w-0"><p className="truncate text-sm font-semibold" title={item.name}>{item.name} <span className={item.is_active ? "text-emerald-700" : "text-[#756F60]"}>· {item.is_active ? "Active" : "Paused"}</span></p><p className="mt-1 truncate text-xs text-[#756F60]" title={item.url}>{item.url}</p><p className="mt-1 truncate text-[11px] text-[#756F60]">{item.events.join(", ")} · failures {item.failure_count}</p></div>
              <button type="button" disabled={deleting} onClick={() => setPendingDelete({ type: "webhook", uuid: item.uuid, name: item.name })} className="shrink-0 text-red-700 disabled:opacity-50" aria-label={`Delete ${item.name}`}><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
          {!webhooks.isLoading && !webhooks.data?.items.length && <p className="py-6 text-center text-sm text-[#756F60]">No webhook endpoints configured.</p>}
        </div>
      </section>
    </div>
  );
}
