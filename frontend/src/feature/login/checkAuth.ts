import { getCurrentUser } from "../../shared/api/authApi";
import { useAuthStore } from "../../shared/store/AuthStore";

export async function checkAuth() {
  const store = useAuthStore.getState();

  try {
    const user = await getCurrentUser();

    store.setUser(user);

    return user;
  } catch {
    store.logout();

    return null;
  }
}
