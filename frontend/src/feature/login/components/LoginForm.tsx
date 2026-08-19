import { useState } from "react";
import { useForm } from "react-hook-form";
import type { SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import mailicon from "../../../assets/Background.svg";
import emailcontainer from "../../../assets/Container.svg";
import passwordIcon from "../../../assets/password.svg";
import right from "../../../assets/right.svg";
import google from "../../../assets/Google.png";
import { Link, useNavigate } from "@tanstack/react-router";
import { useLogin } from "../hooks/useLoginHooks";
import { LoginSchema, type LoginFormData } from "../schema/LoginSchema";
import { Eye, EyeOff } from "lucide-react";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { storePending2FAToken } from "../../../shared/auth/pending2FA";

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(LoginSchema),
  });

  const { mutate, isPending, error } = useLogin();
  const backendErrorMessage = error
    ? getApiErrorMessage(error, "")
    : undefined;
  const oauthSearch = new URLSearchParams(window.location.search);
  const oauthErrorCode = oauthSearch.get("error");
  const oauthErrorDetail = oauthSearch.get("message")?.trim();
  const oauthErrorMessage = oauthErrorDetail || (oauthErrorCode
    ? ({
        oauth_denied: "Google sign-in was cancelled or denied.",
        oauth_invalid_callback: "Google returned an incomplete sign-in response. Please try again.",
        oauth_callback_failed: "Google sign-in could not be verified. Please try connecting again.",
      } as Record<string, string>)[oauthErrorCode] || "Google sign-in failed. Please try again."
    : undefined);

  const onsubmit: SubmitHandler<LoginFormData> = (data) => {
    mutate(data, {
      onSuccess: (envelope) => {
        if (envelope?.data?.requires_email_verification) {
          return;
        }

        if (envelope?.data?.requires_2fa && envelope?.data?.temp_token) {
          // Keep the short-lived 2FA exchange token out of the URL/history.
          storePending2FAToken(envelope.data.temp_token);
          navigate({
            to: "/verify-2fa",
            search: {},
          });
        }
      },
    });
  };

  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/oauth/login/google`;
  };

  return (
    <>
      <div className="w-full relative min-h-screen overflow-hidden bg-surface px-margin-mobile">
        {/* Ambient background blur */}
        <div className="absolute -top-20 -left-32 rounded-xl w-96 h-96 bg-[#E5C52B33] blur-[120px]"></div>
        <div className="absolute -bottom-1.5 left-2/5 rounded-xl w-80 h-80 bg-[#D7C6851A] blur-[100px]"></div>
        <div className="absolute bottom-10 -right-28 rounded-xl w-125 h-125 bg-[#A8C9F726] blur-[150px]"></div>

        {/* Content Container */}
        <div className="flex flex-col gap-stack-lg max-w-130 mx-auto py-17.5 relative z-10">
          {/* Logo Header */}
          <div className="flex flex-col pb-stack-sm mx-auto">
            <img
              src={mailicon}
              alt="MailTracko Logo"
              className="w-16 mx-auto"
            />
            <span className="text-on-surface font-sans text-center tracking-[-0.6px] text-headline-md font-bold mt-2">
              MailTracko
            </span>
            <span className="font-sans text-body-sm text-center text-[#4B4738] mt-1">
              Enterprise Email Intelligence
            </span>
          </div>

          {/* Form Container */}
          <div className="relative w-full">
            <div className="w-full h-1 bg-[#8F740D] absolute left-0 rounded-tr-lg rounded-tl-lg"></div>
            <div className="w-full rounded-lg border border-[#CDC6B24D] shadow-lg p-8 bg-white flex flex-col gap-5">

              <div className="flex flex-col gap-1 text-center">
                <span className="text-title-sm text-on-surface font-semibold">
                  Welcome back
                </span>
                <span className="text-body-sm text-[#4B4738]">
                  Please enter your details to sign in.
                </span>
              </div>

              <div className="pt-stack-sm">
                <form onSubmit={handleSubmit(onsubmit)}>
                  <div className="flex flex-col gap-stack-md">
                    {/* Work Email Field */}
                    <div className="flex flex-col gap-stack-sm">
                      <label
                        htmlFor="email"
                        className="text-[#4B4738] text-xs font-bold text-label-caps"
                      >
                        Work Email
                      </label>
                      <label htmlFor="email" className="w-full flex cursor-text gap-2.5 items-center border border-[#CEC6B0] bg-surface-container-low rounded-lg py-3 px-4 focus-within:border-[#8F740D] focus-within:bg-white focus-within:ring-2 focus-within:ring-[#F1D442]/30 transition-all">
                        <img
                          src={emailcontainer}
                          alt="Email"
                          className="w-[16.67px] h-5 opacity-70 shrink-0"
                        />
                        <input
                          id="email"
                          placeholder="name@company.com"
                          type="email"
                          autoComplete="email"
                          maxLength={254}
                          {...register("email")}
                          className="w-full bg-transparent border-0 outline-none text-on-surface leading-normal text-sm"
                        />
                      </label>
                      {errors.email && (
                        <p className="text-xs text-red-600 font-medium">
                          {errors.email.message}
                        </p>
                      )}
                    </div>

                    {/* Password Field */}
                    <div className="flex flex-col gap-stack-sm">
                      <div className="w-full flex justify-between items-center">
                        <label
                          htmlFor="password"
                          className="text-[#4B4738] text-xs font-bold text-label-caps"
                        >
                          Password
                        </label>
                        <Link
                          to="/ForgotPassword"
                          className="text-[#8F740D] text-xs font-bold hover:underline"
                        >
                          Forgot password?
                        </Link>
                      </div>

                      <div
                        onClick={(event) => {
                          if (!(event.target as HTMLElement).closest("button")) {
                            document.getElementById("password")?.focus();
                          }
                        }}
                        className="relative flex cursor-text gap-2.5 items-center border border-[#CEC6B0] bg-surface-container-low rounded-lg py-3 pl-4 pr-12 focus-within:border-[#8F740D] focus-within:bg-white focus-within:ring-2 focus-within:ring-[#F1D442]/30 transition-all"
                      >
                        <img
                          src={passwordIcon}
                          alt="Password"
                          className="w-[13.33px] h-5 opacity-70 shrink-0"
                        />
                        <input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••"
                          autoComplete="current-password"
                          maxLength={128}
                          {...register("password")}
                          className="w-full bg-transparent border-0 outline-none text-on-surface leading-normal text-sm"
                        />

                        <button
                          type="button"
                          onClick={() => setShowPassword((prev) => !prev)}
                          className="absolute right-4 text-[#4C4736] hover:text-[#8F740D] transition-colors cursor-pointer"
                          aria-label={
                            showPassword ? "Hide password" : "Show password"
                          }
                        >
                          {showPassword ? (
                            <Eye className="w-4 h-4" />
                          ) : (
                            <EyeOff className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      {errors.password && (
                        <p className="text-xs text-red-600 font-medium">
                          {errors.password.message}
                        </p>
                      )}

                      {(backendErrorMessage || oauthErrorMessage) && (
                        <p className="text-xs text-red-600 font-medium mt-1" role="alert">
                          {backendErrorMessage || oauthErrorMessage}
                        </p>
                      )}
                    </div>

                    {/* Sign In button */}
                    <div className="pt-2">
                      <button
                        type="submit"
                        disabled={isPending}
                        className="w-full flex justify-center items-center gap-2 rounded-lg bg-[#8F740D] hover:bg-[#6E5E00] py-3.5 text-white text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer disabled:opacity-75"
                      >
                        {isPending ? "Signing In..." : "Sign In"}
                        <img
                          src={right}
                          alt="arrow"
                          className="w-3 text-white brightness-0 invert"
                        />
                      </button>
                    </div>
                  </div>
                </form>
              </div>

              {/* Divider */}
              <div className="w-full py-2 flex items-center">
                <div className="flex-1 h-px bg-[#EEEEEE]"></div>
                <span className="px-3 text-[#4C4736] text-[10px] font-bold tracking-wider text-label-caps">
                  OR CONTINUE WITH
                </span>
                <div className="flex-1 h-px bg-[#EEEEEE]"></div>
              </div>

              {/* OAuth buttons */}
              <div className="w-full flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  onClick={handleGoogleLogin}
                  className="w-full rounded-lg border border-[#CEC6B0] hover:bg-surface-container-low transition-colors bg-white flex items-center justify-center gap-2.5 py-3 cursor-pointer"
                >
                  <img src={google} alt="Google" className="w-4 h-4" />
                  <span className="text-xs font-semibold text-[#1A1C1C]">
                    Google
                  </span>
                </button>

              </div>
            </div>
          </div>

          {/* Registration link */}
          <div className="text-[#4C4736] flex justify-center items-center gap-1.5 mt-2">
            <span className="text-xs sm:text-sm">Don't have an account?</span>
            <Link
              to="/register"
              className="font-bold text-xs sm:text-sm text-[#8F740D] hover:underline"
            >
              Create an account
            </Link>
          </div>

          {/* Footer links */}
          <div className="flex justify-center gap-4 text-xs text-[#4C4736]/70 border-t border-[#EEEEEE] pt-4 mt-2">
            <a href="https://mailtracko.com/privacy" className="hover:underline hover:text-[#8F740D]">
              Privacy Policy
            </a>
            <span>·</span>
            <a href="https://mailtracko.com/terms" className="hover:underline hover:text-[#8F740D]">
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </>
  );
}
