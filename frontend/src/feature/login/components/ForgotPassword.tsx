import { Link } from "@tanstack/react-router";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { forgotPasswordSchema, type forgotPasswordFormData } from "../schema/forgotPasswordSchema";
import { useForgotPassword } from "../hooks/useForgotPassword";
import { Mail, ArrowLeft, RefreshCw } from "lucide-react";

export default function ForgotPassword() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<forgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const { mutate, isPending, isError } = useForgotPassword();

  const onSubmit: SubmitHandler<forgotPasswordFormData> = (data) => {
    mutate(data);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-margin-mobile py-stack-lg">
      <div className="w-full max-w-115 rounded-xl border border-[#CEC6B0]/40 bg-white shadow-lg overflow-hidden">
        
        {/* Top Border Accent */}
        <div className="h-1 w-full bg-[#8F740D]" />

        <div className="p-8 space-y-6">
          {/* Logo & Subtext */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-extrabold text-on-surface tracking-tight">
              MailTracko
            </h1>
            <p className="text-xs text-on-surface-variant font-medium">
              Recover your enterprise account access.
            </p>
          </div>

          {/* Reset Icon Badge */}
          <div className="flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-surface-container-low border border-outline-variant/40 shadow-inner">
              <RefreshCw className="w-6 h-6 text-primary animate-spin-slow" />
            </div>
          </div>

          {/* Heading */}
          <div className="text-center space-y-2">
            <h2 className="text-lg font-bold text-on-surface">Forgot Password</h2>
            <p className="text-xs text-on-surface-variant leading-relaxed max-w-xs mx-auto">
              Enter the email associated with your account and we'll send a secure reset link.
            </p>
          </div>

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-on-surface-variant text-label-caps">
                Email Address
              </label>

              <div className="relative flex items-center">
                <Mail className="absolute left-3 w-4 h-4 text-on-surface-variant/80 pointer-events-none" />
                <input
                  type="email"
                  {...register("email")}
                  placeholder="name@company.com"
                  className="w-full border border-outline-variant/60 focus:border-primary rounded-lg pl-9 pr-3 py-2 text-sm text-on-surface bg-surface-container-low focus:bg-white focus:outline-none transition-all"
                />
              </div>
              
              {errors.email && (
                <p className="text-xs text-red-600 font-medium">
                  {errors.email.message}
                </p>
              )}
            </div>

            {isError && (
              <p className="text-xs text-red-600 font-medium text-center">
                Failed to send reset link. Please check your email or try again.
              </p>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary hover:bg-[#6E5E00] py-3 text-sm font-bold text-on-primary shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
            >
              {isPending ? "Sending Link..." : "Send Reset Link"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <hr className="border-outline-variant/60" />

          {/* Back to Login */}
          <Link
            to="/login"
            className="flex w-full items-center justify-center gap-1.5 text-xs font-bold text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Login</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

// Simple Helper Component
function ArrowRight(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2.5}
      stroke="currentColor"
      className="w-4 h-4"
      {...props}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
    </svg>
  );
}
