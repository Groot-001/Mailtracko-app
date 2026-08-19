import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import SuccessForgotPassword from "../feature/login/components/SuccessForgotPassword";

const successForgotPasswordSearchSchema = z.object({
  email: z.string().email().optional().catch(undefined),
});

function SuccessForgotPasswordRoute() {
  const { email } = Route.useSearch();
  return <SuccessForgotPassword email={email} />;
}

export const Route = createFileRoute("/successForgotPassword")({
  validateSearch: successForgotPasswordSearchSchema,
  component: SuccessForgotPasswordRoute,
});
