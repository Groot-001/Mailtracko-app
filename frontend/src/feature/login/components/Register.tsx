import { useState, useEffect } from "react";
import { Eye, EyeOff, User, Mail, Lock, Loader2 } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useCreateAccount } from "../hooks/useregister";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createAccountSchema, type createAccountFormData } from "../schema/register";
import type { SubmitHandler } from "react-hook-form";
import { Route as RegisterRoute } from "../../../routes/register";
import { useInviteValidation } from "../hooks/useInviteValidation";
import { getApiErrorMessage } from "../../../shared/utils/apiError";

export default function CreateAccount() {
  const [showPassword, setShowPassword] = useState(false);
  const { mutate, isPending, isError, error } = useCreateAccount();
  const backendErrorMessage = error ? getApiErrorMessage(error, '') : undefined

  const { token } = RegisterRoute.useSearch();
  const { data: inviteData, error: inviteError, isValidating } = useInviteValidation(token)
  const orgName = inviteData?.organization_name ?? null
  const validationError = inviteError ? getApiErrorMessage(inviteError, 'Invalid or expired invitation token. Please check the URL or ask the organization owner for a new invite.') : null

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<createAccountFormData>({
    resolver: zodResolver(createAccountSchema),
  });

  useEffect(() => {
    if (inviteData?.email) {
      setValue("email", inviteData.email)
    }
  }, [inviteData?.email, setValue])

  const onSubmit: SubmitHandler<createAccountFormData> = (data) => {
    mutate({
      ...data,
      invite_token: token,
    });
  };

  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/oauth/login/google`;
  };

  if (isValidating) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-semibold text-on-surface">Validating invitation details...</p>
        </div>
      </div>
    );
  }

  if (validationError) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="text-red-600 bg-red-50 p-3 rounded-full border border-red-200">
            <Mail className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Invalid Invitation</h2>
          <p className="text-xs text-on-surface-variant max-w-sm leading-relaxed">
            {validationError}
          </p>
          <Link
            to="/register"
            className="mt-2 text-xs font-bold text-primary hover:underline"
          >
            Go to standard sign up
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
      <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg overflow-hidden">

        {/* Header */}
        <div className="text-center pt-stack-lg pb-stack-md px-gutter">
          <h1 className="text-2xl font-extrabold text-on-surface tracking-tight">
            MailTracko
          </h1>
          <p className="text-xs text-on-surface-variant mt-1.5 font-medium tracking-wide">
            ENTERPRISE EMAIL INTELLIGENCE
          </p>
        </div>

        {/* Promo banner */}
        {orgName ? (
          <div className="bg-primary text-on-primary text-center py-stack-sm px-gutter mb-6">
            <p className="text-body-md font-bold">
              Joining {orgName}
            </p>
            <p className="text-xs opacity-90">
              Accepting invitation · Free member account
            </p>
          </div>
        ) : (
          <div className="bg-primary text-on-primary text-center py-stack-sm px-gutter mb-6">
            <p className="text-body-md font-bold">
              Start your 14-day free trial
            </p>
            <p className="text-xs opacity-90">
              No credit card required · Instant setup
            </p>
          </div>
        )}

        <div className="px-gutter pb-stack-lg space-y-5">
          {/* OAuth buttons */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleGoogleLogin}
              className="flex-1 flex items-center justify-center gap-2 border border-outline-variant rounded-lg py-2.5 text-xs font-semibold text-on-surface hover:bg-surface-container-low transition-colors cursor-pointer"
            >
              <img
                src="https://www.google.com/favicon.ico"
                alt="Google"
                className="w-4 h-4"
                aria-hidden="true"
              />
              Google
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <hr className="flex-1 border-outline-variant/60" />
            <span className="text-xs font-semibold text-on-surface-variant text-label-caps">
              OR USE EMAIL
            </span>
            <hr className="flex-1 border-outline-variant/60" />
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface-variant block text-label-caps">
                Full Name
              </label>
              <div className="relative flex items-center">
                <User className="absolute left-3 w-4 h-4 text-on-surface-variant/80 pointer-events-none" />
                <input
                  {...register("full_name")}
                  maxLength={50}
                  placeholder="Johnathan Doe"
                  className="w-full border border-outline-variant/60 focus:border-primary rounded-lg pl-9 pr-3 py-2 text-sm text-on-surface bg-surface-container-low focus:bg-white focus:outline-none transition-all"
                />
              </div>
              {errors.full_name && (
                <p className="text-xs text-red-600 font-medium">
                  {errors.full_name.message}
                </p>
              )}
            </div>

            {/* Work Email */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface-variant block text-label-caps">
                Work Email
              </label>
              <div className="relative flex items-center">
                <Mail className="absolute left-3 w-4 h-4 text-on-surface-variant/80 pointer-events-none" />
                <input
                  {...register("email")}
                  placeholder="john@company.com"
                  readOnly={!!token}
                  className={`w-full border rounded-lg pl-9 pr-3 py-2 text-sm text-on-surface transition-all focus:outline-none ${
                    token
                      ? "bg-surface-container-low/50 text-on-surface-variant cursor-not-allowed border-outline-variant/30"
                      : "border-outline-variant/60 focus:border-primary bg-surface-container-low focus:bg-white"
                  }`}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-red-600 font-medium">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-on-surface-variant block text-label-caps">
                Password
              </label>
              <div className="relative flex items-center">
                <Lock className="absolute left-3 w-4 h-4 text-on-surface-variant/80 pointer-events-none" />
                <input
                  {...register("password")}
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="w-full border border-outline-variant/60 focus:border-primary rounded-lg pl-9 pr-10 py-2 text-sm text-on-surface bg-surface-container-low focus:bg-white focus:outline-none transition-all"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <Eye className="w-4 h-4" />
                  ) : (
                    <EyeOff className="w-4 h-4" />
                  )}
                </button>
              </div>

              {errors.password ? (
                <p className="text-xs text-red-600 font-medium">
                  {errors.password.message}
                </p>
              ) : backendErrorMessage && backendErrorMessage.toLowerCase().includes("password") ? (
                <p className="text-xs text-red-600 font-medium">
                  {backendErrorMessage}
                </p>
              ) : (
                <p className="text-[10px] text-on-surface-variant/80">
                  Must be at least 12 characters including a symbol.
                </p>
              )}
            </div>

            {isError && (
              <p className="text-xs text-red-600 font-medium text-center">
                {backendErrorMessage || "Registration failed. Please check your credentials and try again."}
              </p>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isPending}
              className="w-full bg-primary hover:bg-[#6E5E00] text-on-primary rounded-lg py-2.5 text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
            >
              {isPending ? "Creating account..." : "Create Account"}
            </button>
          </form>

          {/* Registration redirects */}
          <p className="text-center text-xs text-on-surface-variant">
            Already have an account?{" "}
            <Link to="/login" className="font-bold text-primary hover:underline">
              Sign in
            </Link>
          </p>

          <p className="text-center text-[10px] text-on-surface-variant/80 leading-relaxed">
            By signing up, you agree to MailTracko's{" "}
            <a href="https://mailtracko.com/terms" className="underline font-medium text-primary hover:text-[#6E5E00]">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="https://mailtracko.com/privacy" className="underline font-medium text-primary hover:text-[#6E5E00]">
              Privacy Policy
            </a>
            . We strictly respect your inbox and data privacy.
          </p>
        </div>

        {/* Footer banner */}
        <div className="flex items-center justify-between px-gutter py-3 bg-surface-container-low text-xs text-on-surface-variant/90 border-t border-[#CEC6B0]/20">
          <span className="font-medium">Trusted by 2,000+ teams</span>
          <a href="https://mailtracko.com/help-center" className="font-bold text-primary hover:underline">
            Need help?
          </a>
        </div>
      </div>
    </div>
  );
}
