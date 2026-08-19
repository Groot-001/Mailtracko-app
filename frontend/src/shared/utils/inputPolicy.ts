const TEXT_INPUT_TYPES = new Set(["", "text", "search", "email", "password", "url", "tel"]);

const defaultLimitForInput = (input: HTMLInputElement): number | null => {
  const type = input.type.toLowerCase();
  if (!TEXT_INPUT_TYPES.has(type)) return null;
  if (type === "search") return 100;
  if (type === "email") return 254;
  if (type === "password") return 128;
  if (type === "url") return 2048;
  if (type === "tel") return 32;
  return 255;
};

const applyLimit = (element: Element) => {
  if (element instanceof HTMLInputElement) {
    if (element.hasAttribute("maxlength")) return;
    const limit = defaultLimitForInput(element);
    if (limit) element.maxLength = limit;
    return;
  }

  if (element instanceof HTMLTextAreaElement && !element.hasAttribute("maxlength")) {
    // Explicit component/schema limits always take precedence. This is the
    // product-wide safety ceiling for free-form fields that omitted one.
    element.maxLength = 5000;
  }
};

const scan = (root: ParentNode) => {
  if (root instanceof Element) applyLimit(root);
  root.querySelectorAll?.("input, textarea").forEach(applyLimit);
};

/**
 * Enforce a defensive character-limit policy for all current and dynamically
 * mounted text inputs. Feature-specific maxLength values remain authoritative.
 */
export const installGlobalInputPolicy = () => {
  scan(document);
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (node instanceof Element) scan(node);
      });
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  // Compound fields often render an icon + a border shell + the actual input.
  // Make the shell padding/icon area focus the control too, while never
  // stealing clicks from buttons, links, or other interactive elements.
  const focusCompoundField = (event: MouseEvent) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target || target.closest("button, a, input, textarea, select, [role='button']")) return;

    const shell = target.closest("label, div[class*='border']");
    if (!shell) return;
    const control = shell.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
      ":scope > input:not([type='checkbox']):not([type='radio']):not([type='file']), :scope > textarea, :scope > select",
    );
    if (control && !control.disabled) control.focus();
  };

  document.addEventListener("click", focusCompoundField);
  return () => {
    observer.disconnect();
    document.removeEventListener("click", focusCompoundField);
  };
};
