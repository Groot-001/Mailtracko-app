import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { AlertTriangle, RotateCw, Loader2, Check, Link2 } from "lucide-react";
import { useConnectSMTP } from "../hooks/useEmailAccounts";
import { testSMTPCredentials } from "../api/emailAccountsApi";
import type { SMTPConnectPayload } from "../types/email-accounts.types";
import { getApiErrorMessage, getApiFieldErrors } from "../../../shared/utils/apiError";
import { normalizePort, smtpFormSchema, type SmtpFormValues } from "../schema/smtpSchema";

interface SMTPFormModalProps {
  onClose: () => void;
  onBack: () => void;
  onSuccess: (uuid: string, email: string) => void;
}

type ConnectionStatus = "untested" | "testing" | "verified" | "failed";

const fieldClass = (hasError?: boolean) =>
  `w-full rounded-xl border bg-white px-3 py-2 text-xs outline-none transition focus:ring-1 ${hasError ? "border-red-400 focus:border-red-500 focus:ring-red-300/30" : "border-[#CEC6B0]/60 focus:border-[#8F740D] focus:ring-[#F1D442]/30"}`;

const FieldError = ({ message }: { message?: string }) =>
  message ? <p role="alert" className="text-[10px] font-medium leading-4 text-red-600">{message}</p> : null;

export const SMTPFormModal = ({ onClose, onBack, onSuccess }: SMTPFormModalProps) => {
  const connectMutation = useConnectSMTP();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("untested");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    setError,
    trigger,
    watch,
    formState: { errors },
  } = useForm<SmtpFormValues>({
    resolver: zodResolver(smtpFormSchema),
    mode: "onBlur",
    reValidateMode: "onChange",
    defaultValues: {
      sender_name: "",
      email: "",
      smtp_host: "",
      smtp_port: "587",
      smtp_username: "",
      smtp_password: "",
      imap_host: "",
      imap_port: "993",
    },
  });

  const smtpPort = watch("smtp_port");
  const imapPort = watch("imap_port");

  useEffect(() => {
    const subscription = watch(() => {
      setErrorMessage(null);
      setConnectionStatus((current) => current === "verified" || current === "failed" ? "untested" : current);
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  const toCredentials = (values: SmtpFormValues): SMTPConnectPayload => ({
    email: values.email.trim(),
    sender_name: values.sender_name.trim() || values.email.split("@")[0],
    smtp_host: values.smtp_host.trim(),
    smtp_port: Number(values.smtp_port),
    smtp_username: values.smtp_username.trim(),
    smtp_password: values.smtp_password,
    imap_host: values.imap_host.trim() || undefined,
    imap_port: values.imap_host.trim() ? Number(values.imap_port) : undefined,
  });

  const attachBackendFieldErrors = (error: unknown) => {
    const backendErrors = getApiFieldErrors(error);
    const knownFields = new Set(["sender_name", "email", "smtp_host", "smtp_port", "smtp_username", "smtp_password", "imap_host", "imap_port"]);
    let attached = false;
    for (const [path, message] of Object.entries(backendErrors)) {
      const field = path.split(".").filter(Boolean).at(-1) as keyof SmtpFormValues | undefined;
      if (field && knownFields.has(field)) {
        setError(field, { type: "server", message });
        attached = true;
      }
    }
    return attached;
  };

  const handleTestConnection = async () => {
    const valid = await trigger();
    if (!valid) {
      setConnectionStatus("untested");
      return;
    }

    setConnectionStatus("testing");
    setErrorMessage(null);
    try {
      await testSMTPCredentials(toCredentials(getValues()));
      setConnectionStatus("verified");
    } catch (error: unknown) {
      if (attachBackendFieldErrors(error)) {
        setErrorMessage(null);
        setConnectionStatus("untested");
      } else {
        setErrorMessage(getApiErrorMessage(error, "The mail server rejected these credentials."));
        setConnectionStatus("failed");
      }
    }
  };

  const submit = handleSubmit(async (values) => {
    if (connectionStatus !== "verified") return;
    setErrorMessage(null);
    try {
      const res = await connectMutation.mutateAsync(toCredentials(values));
      onSuccess(res.uuid, values.email.trim());
    } catch (error: unknown) {
      if (attachBackendFieldErrors(error)) {
        setErrorMessage(null);
        setConnectionStatus("untested");
      } else {
        setErrorMessage(getApiErrorMessage(error, "SMTP authentication failed. Please check your server settings and credentials."));
        setConnectionStatus("failed");
      }
    }
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="relative max-h-[90vh] w-full max-w-xl space-y-5 overflow-y-auto rounded-2xl border border-[#CEC6B0]/40 bg-white p-6 shadow-xl animate-in zoom-in-95 duration-200">
        <button type="button" onClick={onClose} className="absolute right-4 top-4 text-sm font-semibold text-[#4C4736] hover:text-[#1A1C1C]" aria-label="Close SMTP setup">✕</button>

        <div>
          <h3 className="text-base font-bold text-[#1A1C1C]">Connect Custom Account</h3>
          <p className="mt-0.5 text-xs text-[#4C4736]">Configure your SMTP and optional IMAP settings manually.</p>
        </div>

        <form onSubmit={submit} className="space-y-4 text-xs text-[#1A1C1C]" noValidate>
          <div className="space-y-3">
            <h4 className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#4C4736]">Sender Account Information</h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="min-w-0 space-y-1" htmlFor="sender-name-field">
                <span className="font-semibold">Sender Name</span>
                <input id="sender-name-field" type="text" placeholder="Sender display name" maxLength={50} {...register("sender_name")} aria-invalid={Boolean(errors.sender_name)} className={fieldClass(Boolean(errors.sender_name))} />
                <FieldError message={errors.sender_name?.message} />
              </label>
              <label className="min-w-0 space-y-1" htmlFor="email-address-field">
                <span className="font-semibold">Email Address *</span>
                <input id="email-address-field" type="email" placeholder="sender@your-domain.tld" maxLength={254} {...register("email")} aria-invalid={Boolean(errors.email)} className={fieldClass(Boolean(errors.email))} />
                <FieldError message={errors.email?.message} />
              </label>
            </div>
          </div>

          <div className="space-y-3 border-t border-[#F4F3F3] pt-3">
            <h4 className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#4C4736]">SMTP Configuration (Outgoing)</h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className="min-w-0 space-y-1 sm:col-span-2" htmlFor="smtp-host-field">
                <span className="font-semibold">SMTP Host *</span>
                <input id="smtp-host-field" type="text" placeholder="smtp.your-domain.tld" maxLength={253} {...register("smtp_host")} aria-invalid={Boolean(errors.smtp_host)} className={fieldClass(Boolean(errors.smtp_host))} />
                <FieldError message={errors.smtp_host?.message} />
              </label>
              <label className="min-w-0 space-y-1" htmlFor="smtp-port-field">
                <span className="font-semibold">Port *</span>
                <input
                  id="smtp-port-field"
                  type="text"
                  inputMode="numeric"
                  value={smtpPort}
                  {...register("smtp_port")}
                  onChange={(event) => setValue("smtp_port", normalizePort(event.target.value), { shouldDirty: true, shouldValidate: true })}
                  onBlur={(event) => setValue("smtp_port", normalizePort(event.target.value), { shouldDirty: true, shouldValidate: true })}
                  aria-invalid={Boolean(errors.smtp_port)}
                  className={fieldClass(Boolean(errors.smtp_port))}
                />
                <FieldError message={errors.smtp_port?.message} />
              </label>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="min-w-0 space-y-1" htmlFor="smtp-username-field">
                <span className="font-semibold">SMTP Username *</span>
                <input id="smtp-username-field" type="text" placeholder="Often your email" maxLength={255} {...register("smtp_username")} aria-invalid={Boolean(errors.smtp_username)} className={fieldClass(Boolean(errors.smtp_username))} />
                <FieldError message={errors.smtp_username?.message} />
              </label>
              <label className="min-w-0 space-y-1" htmlFor="smtp-password-field">
                <span className="font-semibold">SMTP Password *</span>
                <input id="smtp-password-field" type="password" autoComplete="new-password" placeholder="••••••••" maxLength={255} {...register("smtp_password")} aria-invalid={Boolean(errors.smtp_password)} className={fieldClass(Boolean(errors.smtp_password))} />
                <FieldError message={errors.smtp_password?.message} />
              </label>
            </div>
          </div>

          <div className="space-y-3 border-t border-[#F4F3F3] pt-3">
            <h4 className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#4C4736]">IMAP Configuration (Incoming, optional)</h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className="min-w-0 space-y-1 sm:col-span-2" htmlFor="imap-host-field">
                <span className="font-semibold">IMAP Host</span>
                <input id="imap-host-field" type="text" placeholder="imap.your-domain.tld" maxLength={253} {...register("imap_host")} aria-invalid={Boolean(errors.imap_host)} className={fieldClass(Boolean(errors.imap_host))} />
                <FieldError message={errors.imap_host?.message} />
              </label>
              <label className="min-w-0 space-y-1" htmlFor="imap-port-field">
                <span className="font-semibold">Port</span>
                <input
                  id="imap-port-field"
                  type="text"
                  inputMode="numeric"
                  value={imapPort}
                  {...register("imap_port")}
                  onChange={(event) => setValue("imap_port", normalizePort(event.target.value), { shouldDirty: true, shouldValidate: true })}
                  onBlur={(event) => setValue("imap_port", normalizePort(event.target.value), { shouldDirty: true, shouldValidate: true })}
                  aria-invalid={Boolean(errors.imap_port)}
                  className={fieldClass(Boolean(errors.imap_port))}
                />
                <FieldError message={errors.imap_port?.message} />
              </label>
            </div>
          </div>

          {connectionStatus === "untested" && (
            <div className="flex flex-col gap-3 rounded-xl border border-[#CEC6B0]/40 bg-[#F9F9F9] p-3.5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-3 items-center">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#F1D442]/20 text-[#8F740D]"><Link2 className="h-4 w-4" /></div>
                <div><p className="font-bold text-[#1A1C1C]">Test Settings</p><p className="text-[10px] text-[#4C4736]">Validate the form, then verify credentials against the mail server.</p></div>
              </div>
              <button type="button" onClick={() => void handleTestConnection()} className="flex shrink-0 items-center justify-center gap-1.5 rounded-xl border border-[#CEC6B0]/80 bg-white px-3.5 py-1.5 text-[10px] font-bold text-[#8F740D] transition-all hover:border-[#8F740D] hover:text-[#6A5B00]"><RotateCw className="h-3.5 w-3.5" /> Test Connection</button>
            </div>
          )}

          {connectionStatus === "testing" && (
            <div className="flex items-center gap-3 rounded-xl border border-[#CEC6B0]/40 bg-[#F9F9F9] p-3.5"><Loader2 className="h-5 w-5 shrink-0 animate-spin text-[#8F740D]" /><div><p className="font-bold text-[#1A1C1C]">Verifying Credentials</p><p className="text-[10px] text-[#4C4736]">Attempting connection to SMTP/IMAP servers...</p></div></div>
          )}

          {connectionStatus === "failed" && (
            <div className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-3.5 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex gap-3 items-start"><AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" /><div><p className="font-bold text-red-700">Connection failed</p><p className="mt-0.5 text-[10px] leading-relaxed text-red-600">{errorMessage || "Authentication failed. Please check your mail server settings."}</p></div></div>
              <button type="button" onClick={() => void handleTestConnection()} className="flex shrink-0 items-center justify-center gap-1 rounded-lg border border-red-200 bg-white px-3 py-1.5 text-[10px] font-semibold text-red-700 hover:bg-red-50"><RotateCw className="h-3 w-3" /> Retry Test</button>
            </div>
          )}

          {connectionStatus === "verified" && (
            <div className="flex flex-col gap-3 rounded-xl border border-[#F1D442]/40 bg-[#F1D442]/10 p-3.5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-3 items-center"><div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#8F740D]/10 text-[#8F740D]"><Check className="h-4 w-4" /></div><div><p className="font-bold text-[#8F740D]">Connection Verified</p><p className="text-[10px] text-[#4C4736]">Credentials are valid. Connect to save this sender account.</p></div></div>
              <span className="flex shrink-0 items-center justify-center gap-1 rounded-xl bg-[#8F740D] px-3 py-1.5 text-[10px] font-bold text-white"><Check className="h-3.5 w-3.5" /> Connected</span>
            </div>
          )}

          <div className="flex flex-col-reverse gap-3 border-t border-[#F4F3F3] pt-3 sm:flex-row sm:justify-end">
            <button type="button" onClick={onBack} className="rounded-xl border border-[#CEC6B0]/60 px-4 py-2 text-xs font-semibold hover:bg-[#F4F3F3]">Back</button>
            <button type="submit" disabled={connectionStatus !== "verified" || connectMutation.isPending} className="flex items-center justify-center gap-1.5 rounded-xl bg-[#8F740D] px-5 py-2 text-xs font-semibold text-white hover:bg-[#6A5B00] disabled:cursor-not-allowed disabled:opacity-50">
              {connectMutation.isPending ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Connecting...</> : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
