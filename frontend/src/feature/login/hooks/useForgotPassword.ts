import { useMutation } from "@tanstack/react-query";
import { forgotPassword } from "../api/forgotPasswordApi";
import { useNavigate } from "@tanstack/react-router";

export function useForgotPassword() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: forgotPassword,
    onSuccess: (_data, variables) => {
      navigate({
        to: "/ForgotPassword/verify",
        search: {
          email: variables.email,
        },
      });
    },
  });
}
