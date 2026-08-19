import { Check, Loader2, Lock } from "lucide-react";

export default function SuccessfulLogin() {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-margin-mobile">
      <div className="w-full max-w-md">
        <div className="bg-surface-container-lowest rounded-xl shadow-button px-gutter py-stack-lg flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-lg bg-primary-container flex items-center justify-center mb-stack-md">
            <div className="w-9 h-9 rounded-full bg-on-primary-container flex items-center justify-center">
              <Check
                className="w-5 h-5 text-primary-container"
                strokeWidth={3}
              />
            </div>
          </div>

          <h1 className="text-headline-md font-bold text-primary mb-stack-sm">
            Successfully signed in!
          </h1>

          <p className="text-body-sm text-on-surface-variant max-w-xs mb-stack-md">
            Welcome back to your high-performance growth engine.
          </p>

          <div className="bg-surface-container rounded-full px-4 py-2 flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 text-on-surface-variant animate-spin" />
            <span className="text-label-caps text-on-surface-variant">
              Redirecting you to your dashboard...
            </span>
          </div>
        </div>

        <div className="flex flex-col items-center gap-1 mt-stack-md">
          <div className="flex items-center gap-1.5">
            <Lock className="w-3 h-3 text-tertiary" />
            <span className="text-label-caps text-tertiary">
              Securely Encrypted Session
            </span>
          </div>
          <span className="text-body-sm font-semibold text-on-surface-variant">
            MailTracko
          </span>
        </div>
      </div>
    </div>
  );
}
