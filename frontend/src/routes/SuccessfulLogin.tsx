import { createFileRoute } from "@tanstack/react-router";
import SuccessfulLogin from "../feature/login/components/SussessfulSignIn";

export const Route = createFileRoute("/SuccessfulLogin")({
  component: SuccessfulLogin,
});
