import { createFileRoute } from "@tanstack/react-router";
import ForgotPassword from "../../feature/login/components/ForgotPassword";

export const Route = createFileRoute("/ForgotPassword/")({
  component: ForgotPassword,
});
