import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { Send, Info, UserPlus } from "lucide-react";
import { useInviteMember } from "../../hooks/useInvitations";
import type { RoleCode } from "../../types/organization.types";
import { Link } from "@tanstack/react-router";
import { AppSelect } from "../../../../shared/components/AppSelect";
import { useToast } from "../../../../shared/hooks/useToast";
import { getApiErrorMessage } from "../../../../shared/utils/apiError";

// ─── Schema ───────────────────────────────────────────────────────────────────

const inviteSchema = z.object({
  email: z.email("Enter a valid email address"),
  role_code: z.enum(["admin", "member"] as const, {
    error: "Please select a role",
  }),
  department: z.string().optional(),
});

type InviteFormValues = z.infer<typeof inviteSchema>;

// ─── Component ────────────────────────────────────────────────────────────────

interface InvitePanelProps {
  onSuccess?: () => void;
}

export const InvitePanel = ({ onSuccess }: InvitePanelProps) => {
  const inviteMutation = useInviteMember();
  const { showToast } = useToast();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<InviteFormValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      role_code: "member",
    },
  });

  const onSubmit = async (values: InviteFormValues) => {
    try {
      await inviteMutation.mutateAsync({
        email: values.email,
        role_code: values.role_code as RoleCode,
      });
      reset();
      onSuccess?.();
      showToast("Invitation sent successfully", "success");
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, "Failed to send invitation. Please try again."), "error");
    }
  };

  return (
    <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#F4F3F3] flex items-center justify-center flex-shrink-0">
            <UserPlus className="w-4 h-4 text-[#8F740D]" />
          </div>
          <span className="text-sm font-semibold text-[#1A1C1C]">Invite new members</span>
        </div>
        <Link
          to="/organization/team/invite"
          className="text-xs font-bold text-[#8F740D] hover:underline cursor-pointer"
        >
          Use Wizard
        </Link>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {/* Email */}
        <div className="space-y-1.5">
          <label htmlFor="invite-email" className="block text-xs font-semibold text-[#1A1C1C]">
            Email address
          </label>
          <input
            id="invite-email"
            type="email"
            autoComplete="off"
            placeholder="Enter email address"
            {...register("email")}
            className={`w-full px-3 py-2.5 rounded-xl border text-sm text-[#1A1C1C] placeholder:text-[#CEC6B0] focus:outline-none focus:ring-2 transition-all ${errors.email
              ? "border-red-400 focus:ring-red-200"
              : "border-[#CEC6B0]/60 focus:ring-[#F1D442]/50 focus:border-[#8F740D]"
              }`}
          />
          {errors.email && (
            <p className="text-xs text-red-500">{errors.email.message}</p>
          )}
        </div>

        {/* Role */}
        <div className="space-y-1.5">
          <label htmlFor="invite-role" className="block text-xs font-semibold text-[#1A1C1C]">
            Role
          </label>
          <AppSelect value={watch("role_code") || ""} onValueChange={(value) => setValue("role_code", value as "admin" | "member", { shouldDirty: true, shouldValidate: true })} ariaLabel="Invitation role" options={[{ value: "", label: "Select a role" }, { value: "admin", label: "Admin" }, { value: "member", label: "Member" }]} />
          {errors.role_code && (
            <p className="text-xs text-red-500">{errors.role_code.message}</p>
          )}
        </div>

        {/* Department (optional) */}
        <div className="space-y-1.5">
          <label htmlFor="invite-department" className="block text-xs font-semibold text-[#1A1C1C]">
            Team / Department{" "}
            <span className="text-[#4C4736] font-normal">(optional)</span>
          </label>
          <AppSelect value={watch("department") || ""} onValueChange={(value) => setValue("department", value || undefined, { shouldDirty: true })} ariaLabel="Team or department" options={[{ value: "", label: "Select a team or department" }, { value: "engineering", label: "Engineering" }, { value: "marketing", label: "Marketing" }, { value: "sales", label: "Sales" }, { value: "support", label: "Support" }, { value: "design", label: "Design" }]} />
        </div>

        {/* Info note */}
        <div className="flex items-start gap-2 bg-[#F4F3F3] rounded-xl px-3 py-2.5">
          <Info className="w-3.5 h-3.5 text-[#4C4736] flex-shrink-0 mt-0.5" />
          <p className="text-[11px] text-[#4C4736] leading-relaxed">
            An invitation email will be sent to the new member with instructions to join.
          </p>
        </div>

        {/* Submit */}
        <button
          id="send-invite-btn"
          type="submit"
          disabled={isSubmitting || inviteMutation.isPending}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-60"
        >
          <Send className="w-4 h-4" />
          {isSubmitting || inviteMutation.isPending ? "Sending…" : "Send invite"}
        </button>

      </form>
    </div>
  );
};
