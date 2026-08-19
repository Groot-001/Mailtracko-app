const FORCE_LOGIN_KEY = "mailtracko_force_login_until_authenticated";

/**
 * Invitation flows can be opened in a browser that already has another
 * MailTracko session cookie. Keep /login pinned to the login form until a
 * fresh authentication succeeds so a stale session cannot take over again
 * after a refresh/back-navigation.
 */
export const forceNextLoginScreen = () => {
  window.sessionStorage.setItem(FORCE_LOGIN_KEY, "1");
};

export const shouldForceLoginScreen = () =>
  window.sessionStorage.getItem(FORCE_LOGIN_KEY) === "1";

export const clearForcedLoginScreen = () => {
  window.sessionStorage.removeItem(FORCE_LOGIN_KEY);
};
