import { useState, useEffect } from "react";
import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { z } from "zod";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, User, Mail, Lock, Loader2, AlertCircle } from "lucide-react";
import { declineInvite } from "../../feature/login/api/registerApi";
import { useInviteValidation } from "../../feature/login/hooks/useInviteValidation";
import { getApiErrorMessage } from "../../shared/utils/apiError";
import { createAccountSchema, type createAccountFormData } from "../../feature/login/schema/register";
import { useCreateAccount } from "../../feature/login/hooks/useregister";
import { clearPendingInvitationToken, storePendingInvitationToken } from "../../shared/auth/pendingInvitation";
import { forceNextLoginScreen } from "../../shared/auth/forceLogin";

const inviteSearchSchema = z.object({
  token: z.string().catch(""),
});

export const Route = createFileRoute("/invite/")({
  validateSearch: inviteSearchSchema,
  component: InviteLandingPage,
});

function InviteLandingPage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const { data: inviteData, error: inviteError, isValidating } = useInviteValidation(token)
  const orgName = inviteData?.organization_name ?? null
  const validationError = inviteError ? getApiErrorMessage(inviteError, 'Link expired or invalid. Please check the link or ask the organization owner for a new invite.') : null
  const [showPassword, setShowPassword] = useState(false);
  const [isDeclining, setIsDeclining] = useState(false);
  const [declineError, setDeclineError] = useState<string | null>(null);

  const { mutate, isPending, isError } = useCreateAccount();

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
      setValue('email', inviteData.email)
    }
  }, [inviteData?.email, setValue])

  const onSubmit: SubmitHandler<createAccountFormData> = (data) => {
    mutate({
      ...data,
      invite_token: token,
    });
  };

  const handleDecline = async () => {
    if (!token) return;
    try {
      setIsDeclining(true);
      setDeclineError(null);
      await declineInvite(token);
      clearPendingInvitationToken();
      forceNextLoginScreen();
      navigate({ to: "/login", replace: true });
    } catch (error: unknown) {
      setDeclineError(getApiErrorMessage(error, 'Failed to decline the invitation.'))
    } finally {
      setIsDeclining(false);
    }
  };

  if (isValidating) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-[#CEC6B0]/40 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-semibold text-on-surface font-sans">Validating invitation details...</p>
        </div>
      </div>
    );
  }

  if (validationError) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile py-stack-lg">
        <div className="w-full max-w-120 bg-surface-container-lowest border border-red-200 rounded-xl shadow-lg p-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="text-red-600 bg-red-50 p-3 rounded-full border border-red-200">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-on-surface">Invalid Invitation</h2>
          <p className="text-xs text-on-surface-variant max-w-sm leading-relaxed">
            {validationError}
          </p>
          <Link
            to="/login"
            className="mt-2 text-xs font-bold text-primary hover:underline"
          >
            Go to login
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
        <div className="bg-primary text-on-primary text-center py-stack-sm px-gutter mb-6">
          <p className="text-body-md font-bold">
            Joining {orgName}
          </p>
          <p className="text-xs opacity-90">
            Accept your invite to access organization features
          </p>
        </div>

        <div className="px-gutter pb-stack-lg space-y-5">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Organization Name shown as text */}
            {orgName && (
              <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-3 text-center">
                <span className="text-xs text-on-surface-variant block font-bold text-label-caps">Organization</span>
                <span className="text-sm font-semibold text-on-surface mt-0.5 block">{orgName}</span>
              </div>
            )}

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
                  readOnly
                  className="w-full border rounded-lg pl-9 pr-3 py-2 text-sm text-on-surface transition-all focus:outline-none bg-surface-container-low/50 text-on-surface-variant cursor-not-allowed border-outline-variant/30"
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
              ) : (
                <p className="text-[10px] text-on-surface-variant/80">
                  Must be at least 12 characters including a symbol.
                </p>
              )}
            </div>

            {isError && (
              <p className="text-xs text-red-600 font-medium text-center">
                Registration failed. Please check your credentials and try again.
              </p>
            )}
            {declineError && (
              <p role="alert" className="rounded-lg bg-red-50 p-3 text-center text-xs font-medium text-red-700">
                {declineError}
              </p>
            )}

            {/* Action buttons */}
            <div className="flex flex-col gap-2 pt-2">
              <button
                type="submit"
                disabled={isPending || isDeclining}
                className="w-full bg-primary hover:bg-[#6E5E00] text-on-primary rounded-lg py-2.5 text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
              >
                {isPending ? "Joining..." : "Accept & Join"}
              </button>
              
              <button
                type="button"
                onClick={handleDecline}
                disabled={isPending || isDeclining}
                className="w-full text-center text-xs font-bold text-red-600 hover:text-red-800 py-2 transition-colors cursor-pointer disabled:opacity-75"
              >
                {isDeclining ? "Declining..." : "Decline Invitation"}
              </button>
            </div>
          </form>

          {/* Registration redirects */}
          <p className="text-center text-xs text-on-surface-variant">
            Already have an account?{" "}
            <Link
              to="/login"
              onClick={() => { storePendingInvitationToken(token); forceNextLoginScreen(); }}
              className="font-bold text-primary hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
