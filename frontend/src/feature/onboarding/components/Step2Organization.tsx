import { useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Globe,
  Upload,
  Info,
  ArrowRight,
  Lock,
  Sparkles,
  ShieldCheck,
  BarChart3,
  Trash2,
} from "lucide-react";
import {
  ORGANIZATION_SIZE_OPTIONS,
  organizationStepSchema,
  type OrganizationStepFormData,
  type OrganizationStepFormInput,
} from "../schema/onboardingSchema";
import type { OrganizationData } from "../types/onboarding.types";
import { uploadOnboardingLogo } from "../api/onboardingApi";
import { AppSelect } from "../../../shared/components/AppSelect";
import { useToast } from "../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../shared/utils/apiError";

interface Step2OrganizationProps {
  initialValues: OrganizationData;
  onNext: (data: OrganizationData) => void;
  onBack: () => void;
}

const isOrganizationSizeOption = (value: string): value is OrganizationStepFormInput["organizationSize"] =>
  (ORGANIZATION_SIZE_OPTIONS as readonly string[]).includes(value);

export function Step2Organization({
  initialValues,
  onNext,
  onBack,
}: Step2OrganizationProps) {
  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm<OrganizationStepFormInput, unknown, OrganizationStepFormData>({
    resolver: zodResolver(organizationStepSchema),
    defaultValues: {
      organizationName: initialValues.organizationName || "",
      websiteUrl: initialValues.websiteUrl || "",
      organizationSize: isOrganizationSizeOption(initialValues.organizationSize)
        ? initialValues.organizationSize
        : undefined,
      companyEmailDomain: initialValues.companyEmailDomain || "",
      description: initialValues.description || "",
      logoUrl: initialValues.logoUrl || "",
    },
  });

  const formValues = useWatch({ control });
  const logoInputRef = useRef<HTMLInputElement>(null);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [logoError, setLogoError] = useState<string | null>(null);
  const { showToast } = useToast();

  const handleLogoUpload = async (file?: File) => {
    if (!file) return;
    setLogoError(null);
    const allowedTypes = new Set(["image/png", "image/jpeg", "image/webp", "image/svg+xml"]);
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
      const url = await uploadOnboardingLogo(file);
      setValue("logoUrl", url, { shouldDirty: true, shouldValidate: true });
      showToast("Organization logo uploaded successfully.", "success");
    } catch (error: unknown) {
      const message = getApiErrorMessage(error, "Logo upload failed. Please try again.");
      setLogoError(message);
      showToast(message, "error");
    } finally {
      setIsUploadingLogo(false);
      if (logoInputRef.current) logoInputRef.current.value = "";
    }
  };

  const handleFormSubmit = (data: OrganizationStepFormData) => {
    onNext(data);
  };

  // Auto-generate domain slug preview if user types org name
  const handleOrgNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setValue("organizationName", val, { shouldValidate: true });
    if (!formValues.companyEmailDomain) {
      const slug = val.toLowerCase().replace(/[^a-z0-9]/g, "");
      if (slug) setValue("companyEmailDomain", `${slug}.com`);
    }
  };

  return (
    <>
      
    <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      {/* Left Main Form Container */}
      <div className="lg:col-span-8 bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 sm:p-10 shadow-lg space-y-6">
        {/* Step Pill */}
        <div className="inline-block bg-[#F5E29F]/50 text-[#8F740D] border border-[#F2DF9C] px-3 py-1 rounded-full text-xs font-semibold">
          Step 2 of 7
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-[#1A1C1C] tracking-tight">
            Tell us about your organization
          </h1>
          <p className="text-[#4C4736] text-sm leading-relaxed">
            These details help us personalize your experience and keep your
            workspace organized.
          </p>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Organization Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C] flex items-center gap-1.5">
                <span>Organization Name</span>
                <Info className="w-3.5 h-3.5 text-[#4C4736]/60" />
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Your organization"
                  {...register("organizationName")}
                  maxLength={50}
                  onChange={handleOrgNameChange}
                  className="w-full bg-[#F9F9F9] border border-[#CEC6B0]/60 focus:border-[#8F740D] focus:bg-white rounded-xl py-3 px-4 text-sm text-[#1A1C1C] outline-none transition-all"
                />
              </div>
              {errors.organizationName && (
                <p className="text-xs text-red-600 font-medium">
                  {errors.organizationName.message}
                </p>
              )}
            </div>

            {/* Website URL */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C] flex items-center gap-1.5">
                <span>Website URL</span>
                <Info className="w-3.5 h-3.5 text-[#4C4736]/60" />
              </label>
              <div className="relative flex items-center">
                <Globe className="w-4 h-4 text-[#4C4736]/60 absolute left-3.5 pointer-events-none" />
                <input
                  type="text"
                  placeholder="https://yourcompany.com"
                  {...register("websiteUrl")}
                  maxLength={200}
                  className="w-full bg-[#F9F9F9] border border-[#CEC6B0]/60 focus:border-[#8F740D] focus:bg-white rounded-xl py-3 pl-10 pr-4 text-sm text-[#1A1C1C] outline-none transition-all"
                />
              </div>
              {errors.websiteUrl && (
                <p className="text-xs text-red-600 font-medium">
                  {errors.websiteUrl.message}
                </p>
              )}
            </div>

            {/* Organization Size */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C] flex items-center gap-1.5">
                <span>Organization Size</span>
                <Info className="w-3.5 h-3.5 text-[#4C4736]/60" />
              </label>
              <AppSelect
                value={formValues.organizationSize || ""}
                onValueChange={(value) => {
                  setValue(
                    "organizationSize",
                    value as OrganizationStepFormInput["organizationSize"],
                    { shouldDirty: true, shouldValidate: true },
                  );
                }}
                ariaLabel="Organization size"
                options={[
                  { value: "", label: "Select organization size" },
                  { value: "1-10 employees", label: "1-10 employees" },
                  { value: "11-50 employees", label: "11-50 employees" },
                  { value: "51-200 employees", label: "51-200 employees" },
                  { value: "201-500 employees", label: "201-500 employees" },
                  { value: "500-1000 employees", label: "500-1000 employees" },
                  { value: "1000+ employees", label: "1000+ employees" },
                ]}
              />
              {errors.organizationSize && (
                <p className="text-xs font-medium text-red-600">{errors.organizationSize.message}</p>
              )}
            </div>

            {/* Company Email Domain */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C] flex items-center gap-1.5">
                <span>Company Email Domain</span>
                <Info className="w-3.5 h-3.5 text-[#4C4736]/60" />
              </label>
              <input
                type="text"
                placeholder="yourcompany.com"
                {...register("companyEmailDomain")}
                maxLength={253}
                className="w-full bg-[#F9F9F9] border border-[#CEC6B0]/60 focus:border-[#8F740D] focus:bg-white rounded-xl py-3 px-4 text-sm text-[#1A1C1C] outline-none transition-all"
              />
              <p className="text-[11px] text-[#4C4736]/70 italic">
                We'll use this to verify your domain and secure your data.
              </p>
              {errors.companyEmailDomain && (
                <p className="text-xs font-medium text-red-600">{errors.companyEmailDomain.message}</p>
              )}
            </div>

          </div>

          {/* Logo Dropzone & Description */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
            {/* Logo Upload Box */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C]">
                Organization Logo or Workspace Avatar{" "}
                <span className="text-[#4C4736]/60 font-normal">
                  (optional)
                </span>
              </label>
              <input
                ref={logoInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/svg+xml"
                className="hidden"
                onChange={(event) => void handleLogoUpload(event.target.files?.[0])}
              />
              <button
                type="button"
                onClick={() => logoInputRef.current?.click()}
                disabled={isUploadingLogo}
                className="w-full border-2 border-dashed border-[#CEC6B0]/60 rounded-xl p-5 bg-[#F9F9F9] hover:bg-white hover:border-[#8F740D] transition-all flex flex-col items-center justify-center gap-2 text-center cursor-pointer min-h-[110px] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {formValues.logoUrl ? (
                  <img src={formValues.logoUrl} alt="Organization logo preview" className="h-12 max-w-28 object-contain" />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-[#F5E29F]/40 flex items-center justify-center">
                    <Upload className="w-4 h-4 text-[#8F740D]" />
                  </div>
                )}
                <div>
                  <span className="text-xs font-bold text-[#8F740D]">
                    {isUploadingLogo ? "Uploading..." : formValues.logoUrl ? "Change logo" : "Upload logo"}
                  </span>
                  <p className="text-[10px] text-[#4C4736]/70">
                    PNG, JPG, WEBP or SVG. Max 5MB.
                  </p>
                </div>
              </button>
              {formValues.logoUrl ? (
                <button type="button" disabled={isUploadingLogo} onClick={() => { setValue("logoUrl", "", { shouldDirty: true, shouldValidate: true }); setLogoError(null); showToast("Organization logo removed.", "success"); }} className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50">
                  <Trash2 className="h-3.5 w-3.5" /> Remove logo
                </button>
              ) : null}
              {logoError ? <p className="text-xs font-medium text-red-600">{logoError}</p> : null}
            </div>

            {/* Description Textarea */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[#1A1C1C]">
                Description / About your organization{" "}
                <span className="text-[#4C4736]/60 font-normal">
                  (optional)
                </span>
              </label>
              <div className="relative">
                <textarea
                  rows={3}
                  maxLength={250}
                  placeholder="Tell us a bit about your organization and what your team does..."
                  {...register("description")}
                  className="w-full bg-[#F9F9F9] border border-[#CEC6B0]/60 focus:border-[#8F740D] focus:bg-white rounded-xl p-3 text-sm text-[#1A1C1C] outline-none transition-all resize-none"
                />
                <span className="absolute bottom-2.5 right-3 text-[10px] text-[#4C4736]/60">
                  {(formValues.description || "").length}/250
                </span>
              </div>
              {errors.description && (
                <p className="text-xs font-medium text-red-600">{errors.description.message}</p>
              )}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between pt-6 border-t border-[#EEEEEE]">
            <button
              type="button"
              onClick={onBack}
              className="border border-[#CEC6B0] hover:bg-[#EEEEEE] text-[#4C4736] font-semibold text-sm px-6 py-3 rounded-xl transition-all cursor-pointer"
            >
              Back
            </button>

            <button
              type="submit"
              className="bg-[#8F740D] hover:bg-[#6E5E00] text-white font-bold text-sm px-8 py-3 rounded-xl flex items-center gap-2 transition-all shadow-md cursor-pointer"
            >
              <span>Continue</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Right Sidebar Information & Live Preview */}
      <div className="lg:col-span-4 space-y-6">
        {/* Why We Ask This Card */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-[#1A1C1C]">Why we ask this</h3>
          <div className="space-y-4">
            <div className="flex gap-3 items-start">
              <div className="w-8 h-8 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#1A1C1C]">
                  Personalized experience
                </h4>
                <p className="text-[11px] text-[#4C4736] leading-tight">
                  We tailor MailTracko to fit your team and workflows.
                </p>
              </div>
            </div>

            <div className="flex gap-3 items-start">
              <div className="w-8 h-8 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4 h-4 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#1A1C1C]">
                  Secure & verified
                </h4>
                <p className="text-[11px] text-[#4C4736] leading-tight">
                  Domain verification helps protect your data and prevent
                  unauthorized access.
                </p>
              </div>
            </div>

            <div className="flex gap-3 items-start">
              <div className="w-8 h-8 rounded-lg bg-[#F5E29F]/40 flex items-center justify-center shrink-0">
                <BarChart3 className="w-4 h-4 text-[#8F740D]" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-[#1A1C1C]">
                  Smarter insights
                </h4>
                <p className="text-[11px] text-[#4C4736] leading-tight">
                  Organization context helps us deliver more relevant analytics.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Live Workspace Profile Preview */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[#1A1C1C]">
              Workspace profile
            </h3>
            <span className="text-[10px] font-semibold bg-[#F5E29F]/60 text-[#8F740D] px-2 py-0.5 rounded-md">
              Preview
            </span>
          </div>

          <div className="bg-[#F9F9F9] border border-[#EEEEEE] rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#8F740D] text-white font-extrabold flex items-center justify-center text-sm shadow-xs">
                {formValues.organizationName
                  ? formValues.organizationName.charAt(0).toUpperCase()
                  : "?"}
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#1A1C1C]">
                  {formValues.organizationName || "Organization name"}
                </h4>
                <p className="text-[11px] text-[#4C4736]">
                  {formValues.organizationSize || "Size not selected"}
                </p>
                <p className="text-[11px] text-[#8F740D] font-medium">
                  {formValues.companyEmailDomain || "Domain not provided"}
                </p>
              </div>
            </div>

          </div>
        </div>

        {/* Security Banner */}
        <div className="bg-[#F9F9F9] border border-[#CEC6B0]/30 rounded-2xl p-4 flex items-center gap-3">
          <Lock className="w-5 h-5 text-[#8F740D] shrink-0" />
          <div className="text-[11px] text-[#4C4736]">
            <strong>Your security is our priority.</strong> We use
            enterprise-grade encryption and follow best practices.
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
