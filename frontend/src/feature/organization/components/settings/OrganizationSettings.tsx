import { useEffect, useRef, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import {
  Save,
  CircleCheck,
  Calendar,
  Tag,
  Hash,
  ImagePlus,
  Loader2,
  Trash2,
} from "lucide-react";
import {
  useOrganization,
  useEditOrganization,
} from "../../hooks/useOrganization";
import { getBillingOverview } from "../../../platform/api/platformApi";
import { uploadOrganizationLogo } from "../../api/organizationApi";
import { PageContainer } from "../../../../shared/components/layout";
import {
  getApiErrorMessage,
  getApiFieldErrors,
} from "../../../../shared/utils/apiError";
import { useToast } from "../../../../shared/hooks/useToast";
import { AppSelect } from "../../../../shared/components/AppSelect";
import { Modal } from "../../../../shared/components/Modal";
import {
  organizationSettingsSchema,
  type OrganizationSettingsValues,
} from "../../schema/organizationSettingsSchema";

const TIMEZONE_OPTIONS = [
  { value: "UTC", label: "UTC" },
  { value: "US/Eastern", label: "GMT-05:00 Eastern Time (US & Canada)" },
  { value: "US/Central", label: "GMT-06:00 Central Time (US & Canada)" },
  { value: "US/Pacific", label: "GMT-08:00 Pacific Time (US & Canada)" },
  { value: "Europe/London", label: "GMT+00:00 London" },
  { value: "Asia/Kathmandu", label: "GMT+05:45 Kathmandu" },
  { value: "Asia/Tokyo", label: "GMT+09:00 Tokyo" },
];

const inputClass = (hasError = false) =>
  `w-full rounded-xl border bg-white px-3 py-2.5 text-sm text-[#1A1C1C] outline-none transition focus:ring-1 ${
    hasError
      ? "border-red-400 focus:border-red-500 focus:ring-red-300/30"
      : "border-[#CEC6B0]/60 focus:border-[#8F740D] focus:ring-[#F1D442]/30"
  }`;

const FieldError = ({ message }: { message?: string }) =>
  message ? (
    <p role="alert" className="text-xs font-medium text-red-600">
      {message}
    </p>
  ) : null;

const defaultsFromOrganization = (org?: {
  name?: string | null;
  website_url?: string | null;
  domain_email?: string | null;
  timezone?: string | null;
  org_logo?: string | null;
}): OrganizationSettingsValues => ({
  name: org?.name ?? "",
  website_url: org?.website_url ?? "",
  domain_email: org?.domain_email ?? "",
  timezone: org?.timezone ?? "UTC",
  org_logo: org?.org_logo ?? "",
});

export const OrganizationSettings = () => {
  const { data: org, isLoading, isError, error } = useOrganization();
  const editMutation = useEditOrganization();
  const { data: billing } = useQuery({
    queryKey: ["billing", "overview"],
    queryFn: getBillingOverview,
  });
  const { showToast } = useToast();
  const logoInputRef = useRef<HTMLInputElement>(null);
  const formWasInitialized = useRef(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [logoError, setLogoError] = useState<string | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    setError,
    watch,
    formState: { errors, isDirty, isValid },
  } = useForm<OrganizationSettingsValues>({
    resolver: zodResolver(organizationSettingsSchema),
    mode: "onBlur",
    reValidateMode: "onChange",
    defaultValues: defaultsFromOrganization(),
  });

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  useEffect(() => {
    setHasUnsavedChanges(isDirty);
  }, [isDirty]);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

  useEffect(() => {
    if (!org) return;
    if (formWasInitialized.current) return;
    formWasInitialized.current = true;
    reset(defaultsFromOrganization(org));
    setLogoError(null);
  }, [org, reset]);

  const currentName = watch("name");
  const logoUrl = watch("org_logo");
  const timezone = watch("timezone");

  const handleLogoUpload = async (file?: File) => {
    if (!file) return;
    setLogoError(null);
    const allowedTypes = new Set([
      "image/png",
      "image/jpeg",
      "image/webp",
      "image/svg+xml",
    ]);
    if (!allowedTypes.has(file.type)) {
      setLogoError("Choose a PNG, JPG, WEBP, or SVG image.");
      return;
    }
    if (file.size === 0 || file.size > 5 * 1024 * 1024) {
      setLogoError("Logo must be non-empty and 5 MB or smaller.");
      return;
    }

    setIsUploadingLogo(true);
    try {
      const result = await uploadOrganizationLogo(file);
      setValue("org_logo", result.url, {
        shouldDirty: true,
        shouldTouch: true,
        shouldValidate: true,
      });
      showToast(
        "Logo uploaded. Save changes to apply it to the organization.",
        "success",
      );
    } catch (error: unknown) {
      const message = getApiErrorMessage(
        error,
        "Logo upload failed. Please try again.",
      );
      setLogoError(message);
      showToast(message, "error");
    } finally {
      setIsUploadingLogo(false);
      if (logoInputRef.current) logoInputRef.current.value = "";
    }
  };

  const handleRemoveLogo = () => {
    if (!logoUrl || isUploadingLogo || editMutation.isPending) return;
    setValue("org_logo", "", {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    });
    setLogoError(null);
    if (logoInputRef.current) logoInputRef.current.value = "";
  };

  const openCancelModal = () => {
    if (!hasUnsavedChanges) {
      reset(defaultsFromOrganization(org!));
      setLogoError(null);
      return;
    }
    setShowCancelModal(true);
  };

  const confirmCancel = () => {
    if (!org) return;
    reset(defaultsFromOrganization(org));
    setLogoError(null);
    setShowCancelModal(false);
  };

  const save = handleSubmit(async (values) => {
    if (!org) return;
    try {
      await editMutation.mutateAsync({
        uuid: org.uuid,
        payload: {
          name: values.name.trim(),
          website_url: values.website_url.trim() || null,
          domain_email: values.domain_email.trim().toLowerCase() || null,
          timezone: values.timezone.trim(),
          org_logo: values.org_logo.trim() || null,
        },
      });

      // Clear form after successful save
      reset({
        name: "",
        website_url: "",
        domain_email: "",
        timezone: "UTC",
        org_logo: "",
      });
      setLogoError(null);
      showToast("Changes saved successfully.", "success");
    } catch (error: unknown) {
      const backendErrors = getApiFieldErrors(error);
      const knownFields = new Set([
        "name",
        "website_url",
        "domain_email",
        "timezone",
        "org_logo",
      ]);
      let attached = false;
      for (const [path, message] of Object.entries(backendErrors)) {
        const field = path.split(".").filter(Boolean).at(-1) as
          keyof OrganizationSettingsValues | undefined;
        if (field && knownFields.has(field)) {
          setError(field, { type: "server", message });
          attached = true;
        }
      }
      if (!attached)
        showToast(
          getApiErrorMessage(error, "Failed to save organization changes."),
          "error",
        );
    }
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#8F740D] border-t-transparent" />
      </div>
    );
  }

  if (isError) {
    return (
      <PageContainer nested>
        <div className="rounded-xl border border-red-400 bg-red-50 p-4 text-red-700">
          Failed to load organization: {String(error)}
        </div>
      </PageContainer>
    );
  }

  return (
    <>
      <form
        onSubmit={save}
        noValidate
      >
        <PageContainer nested>
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#1A1C1C]">
          Organization Settings
        </h1>
        <p className="mt-1 text-sm text-[#4C4736]">
          Manage your organization details, preferences, and configuration.
        </p>
      </div>

      <div className="grid min-w-0 grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-6">
          <div className="space-y-5 rounded-2xl border border-[#CEC6B0]/40 bg-white p-6">
            <h2 className="text-base font-semibold text-[#1A1C1C]">
              General organization settings
            </h2>

            <div className="space-y-5">
              <div className="space-y-1.5">
                <label
                  htmlFor="org-name"
                  className="block text-sm font-semibold text-[#1A1C1C]"
                >
                  Organization Name *
                </label>
                <p className="text-xs text-[#4C4736]">
                  The official name of your organization.
                </p>
                <input
                  id="org-name"
                  type="text"
                  maxLength={50}
                  {...register("name")}
                  aria-invalid={Boolean(errors.name)}
                  className={inputClass(Boolean(errors.name))}
                />
                <FieldError message={errors.name?.message} />
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="org-logo"
                  className="block text-sm font-semibold text-[#1A1C1C]"
                >
                  Organization Logo
                </label>
                <p className="text-xs text-[#4C4736]">
                  Upload an image or provide a public HTTP/HTTPS URL. JPG, PNG,
                  WEBP, or SVG up to 5 MB.
                </p>
                <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-center">
                  <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center overflow-hidden rounded-xl border border-[#CEC6B0]/40 bg-gradient-to-br from-[#F1D442]/40 to-[#E2C635]/20">
                    {logoUrl ? (
                      <img
                        src={logoUrl}
                        alt={`${currentName || "Organization"} logo`}
                        className="h-full w-full object-contain"
                      />
                    ) : (
                      <span className="text-xl font-black text-[#8F740D]">
                        {currentName.trim().charAt(0).toUpperCase() || "O"}
                      </span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1 space-y-2">
                    <input
                      id="org-logo"
                      type="url"
                      placeholder="https://cdn.your-domain.tld/logo.svg"
                      maxLength={500}
                      {...register("org_logo", {
                        onChange: () => setLogoError(null),
                      })}
                      aria-invalid={Boolean(errors.org_logo)}
                      className={inputClass(Boolean(errors.org_logo))}
                    />
                    <FieldError message={errors.org_logo?.message} />
                    <input
                      ref={logoInputRef}
                      type="file"
                      accept="image/png,image/jpeg,image/webp,image/svg+xml"
                      className="hidden"
                      onChange={(event) =>
                        void handleLogoUpload(event.target.files?.[0])
                      }
                    />
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => logoInputRef.current?.click()}
                        disabled={isUploadingLogo || editMutation.isPending}
                        className="inline-flex items-center gap-2 rounded-xl border border-[#CEC6B0]/60 bg-white px-3 py-2 text-xs font-semibold text-[#1A1C1C] hover:bg-[#F4F3F3] disabled:opacity-60"
                      >
                        {isUploadingLogo ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <ImagePlus className="h-3.5 w-3.5 text-[#8F740D]" />
                        )}
                        {isUploadingLogo ? "Uploading…" : "Upload logo"}
                      </button>
                      {logoUrl ? (
                        <button
                          type="button"
                          onClick={handleRemoveLogo}
                          disabled={isUploadingLogo || editMutation.isPending}
                          className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" /> Remove
                        </button>
                      ) : null}
                    </div>
                    {logoError ? (
                      <p
                        role="alert"
                        className="text-xs font-medium text-red-600"
                      >
                        {logoError}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="org-domain"
                  className="block text-sm font-semibold text-[#1A1C1C]"
                >
                  Website URL
                </label>
                <p className="text-xs text-[#4C4736]">
                  Your primary website URL, including http:// or https://.
                </p>
                <input
                  id="org-domain"
                  type="url"
                  placeholder="https://example.com"
                  maxLength={200}
                  {...register("website_url")}
                  aria-invalid={Boolean(errors.website_url)}
                  className={inputClass(Boolean(errors.website_url))}
                />
                <FieldError message={errors.website_url?.message} />
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="org-email-domain"
                  className="block text-sm font-semibold text-[#1A1C1C]"
                >
                  Company Email Domain
                </label>
                <p className="text-xs text-[#4C4736]">
                  The domain used for your organization email addresses, for
                  example example.com.
                </p>
                <input
                  id="org-email-domain"
                  type="text"
                  inputMode="url"
                  placeholder="example.com"
                  maxLength={253}
                  {...register("domain_email")}
                  aria-invalid={Boolean(errors.domain_email)}
                  className={inputClass(Boolean(errors.domain_email))}
                />
                <FieldError message={errors.domain_email?.message} />
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold text-[#1A1C1C]">
                  Timezone *
                </label>
                <p className="text-xs text-[#4C4736]">
                  Select your organization timezone.
                </p>
                <AppSelect
                  value={timezone}
                  onValueChange={(value) =>
                    setValue("timezone", value, {
                      shouldDirty: true,
                      shouldTouch: true,
                      shouldValidate: true,
                    })
                  }
                  ariaLabel="Organization timezone"
                  searchable
                  options={TIMEZONE_OPTIONS}
                />
                <FieldError message={errors.timezone?.message} />
              </div>
            </div>
          </div>
        </div>

        <div className="min-w-0 space-y-6">
          <div className="space-y-4 rounded-2xl border border-[#CEC6B0]/40 bg-white p-6">
            <h2 className="text-base font-semibold text-[#1A1C1C]">
              Organization summary
            </h2>
            <div className="space-y-4">
              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div
                    className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg ${org?.status === "active" ? "bg-emerald-50" : "bg-amber-50"}`}
                  >
                    <CircleCheck
                      className={`h-4 w-4 ${org?.status === "active" ? "text-emerald-600" : "text-amber-700"}`}
                    />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#1A1C1C]">Status</p>
                    <p className="text-xs text-[#4C4736]">
                      Current workspace availability.
                    </p>
                  </div>
                </div>
                <span
                  className={`inline-flex flex-shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize ${org?.status === "active" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-800"}`}
                >
                  <CircleCheck className="h-3 w-3" />{" "}
                  {org?.status ?? "Unavailable"}
                </span>
              </div>

              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#F4F3F3]">
                    <Calendar className="h-4 w-4 text-[#8F740D]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#1A1C1C]">
                      Created
                    </p>
                    <p className="text-xs text-[#4C4736]">
                      Organization creation date.
                    </p>
                  </div>
                </div>
                <span className="flex-shrink-0 text-sm font-medium text-[#1A1C1C]">
                  {org?.created_at
                    ? new Intl.DateTimeFormat(undefined, {
                        dateStyle: "medium",
                      }).format(new Date(org.created_at))
                    : "Unavailable"}
                </span>
              </div>

              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#F4F3F3]">
                    <Tag className="h-4 w-4 text-[#8F740D]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#1A1C1C]">Plan</p>
                    <p className="text-xs text-[#4C4736]">
                      Current subscription plan.
                    </p>
                  </div>
                </div>
                <span className="min-w-0 break-words text-right text-sm font-medium text-[#1A1C1C]">
                  {billing?.subscription?.plan.name ??
                    billing?.available_plans.find((plan) => plan.is_default)
                      ?.name ??
                    (billing && !billing.billing_enabled
                      ? "Billing disabled"
                      : "No active plan")}
                </span>
              </div>

              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#F4F3F3]">
                    <Hash className="h-4 w-4 text-[#8F740D]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#1A1C1C]">
                      Organization ID
                    </p>
                    <p className="text-xs text-[#4C4736]">
                      Unique identifier for your organization.
                    </p>
                  </div>
                </div>
                <span className="min-w-0 break-all text-right font-mono text-xs text-[#4C4736]">
                  org_{org?.uuid?.slice(0, 12) ?? "…"}
                </span>
              </div>

              <div className="space-y-2 border-t border-[#F4F3F3] pt-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[#4C4736]">
                  Onboarding profile
                </p>
                <div className="grid grid-cols-1 gap-2 text-xs text-[#4C4736]">
                  {[
                    ["Organization size", org?.org_size],
                    ["Monthly volume", org?.monthly_email_volume],
                    ["Industry", org?.industry_sector],
                    ["Source", org?.source],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="flex min-w-0 items-center justify-between gap-3"
                    >
                      <span>{label}</span>
                      <span className="min-w-0 break-words text-right font-medium text-[#1A1C1C]">
                        {value || "—"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-end gap-3 border-t border-[#EEEEEE] bg-white px-4 py-4 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <button
          type="button"
          onClick={openCancelModal}
          disabled={!isDirty || editMutation.isPending || isUploadingLogo}
          className="rounded-xl border border-[#CEC6B0]/60 px-5 py-2.5 text-sm font-medium text-[#1A1C1C] transition-colors hover:bg-[#F4F3F3] disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          id="save-org-settings"
          type="submit"
          aria-busy={editMutation.isPending}
          disabled={!isValid || editMutation.isPending || isUploadingLogo}
          className="inline-flex min-w-[152px] items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#6A5B00] disabled:cursor-not-allowed disabled:bg-[#8F740D] disabled:opacity-50 disabled:hover:bg-[#8F740D]"
        >
          {editMutation.isPending ? (
            <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
          ) : (
            <Save className="h-4 w-4 shrink-0" />
          )}
          <span className="whitespace-nowrap">
            {editMutation.isPending ? "Saving…" : "Save changes"}
          </span>
        </button>
      </div>
        </PageContainer>
      </form>

    <Modal
      open={showCancelModal}
      onClose={() => setShowCancelModal(false)}
      title="Discard unsaved changes?"
      description="You have unsaved changes. Are you sure you want to discard them?"
    >
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => setShowCancelModal(false)}
          className="rounded-xl border border-[#CEC6B0]/60 px-4 py-2.5 text-sm font-medium text-[#514B3C] transition-colors hover:bg-[#F4F3F3]"
        >
          Keep editing
        </button>
        <button
          type="button"
          onClick={confirmCancel}
          disabled={editMutation.isPending}
          className="rounded-xl bg-[#B42318] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
        >
          Discard changes
        </button>
      </div>
    </Modal>
    </>
  );
};