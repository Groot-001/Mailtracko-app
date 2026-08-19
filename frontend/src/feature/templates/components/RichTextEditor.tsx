import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import {
  Bold,
  Code2,
  Italic,
  ImagePlus,
  Link,
  List,
  ListOrdered,
  Redo2,
  Underline,
  Undo2,
} from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import { TextPromptDialog } from "../../../shared/components/TextPromptDialog";
import { uploadTemplateImage } from "../api/templateApi";
import { getApiErrorMessage } from "../../../shared/utils/apiError";

interface RichTextEditorProps {
  value: string;
  onChange: (html: string) => void;
  templateUuid?: string;
  resolveTemplateUuid?: () => Promise<string | null>;
  error?: string;
}

export interface RichTextEditorHandle {
  insertMergeVariable: (variable: string) => void;
}

const commands = [
  { label: "Bold", command: "bold", icon: Bold },
  { label: "Italic", command: "italic", icon: Italic },
  { label: "Underline", command: "underline", icon: Underline },
  { label: "Bullet list", command: "insertUnorderedList", icon: List },
  { label: "Numbered list", command: "insertOrderedList", icon: ListOrdered },
] as const;

const isSafeHttpUrl = (value: string, httpsOnly = false) => {
  try {
    const parsed = new URL(value);
    if (parsed.username || parsed.password) return false;
    return httpsOnly ? parsed.protocol === "https:" : ["https:", "http:"].includes(parsed.protocol);
  } catch {
    return false;
  }
};

const verifyRemoteImage = (url: string) =>
  new Promise<void>((resolve, reject) => {
    const image = new window.Image();
    const timer = window.setTimeout(() => {
      image.src = "";
      reject(new Error("Image verification timed out"));
    }, 8_000);
    image.onload = () => {
      window.clearTimeout(timer);
      if (image.naturalWidth < 1 || image.naturalHeight < 1) {
        reject(new Error("Invalid image dimensions"));
        return;
      }
      resolve();
    };
    image.onerror = () => {
      window.clearTimeout(timer);
      reject(new Error("URL did not load an image"));
    };
    image.referrerPolicy = "no-referrer";
    image.src = url;
  });

export const RichTextEditor = forwardRef<RichTextEditorHandle, RichTextEditorProps>(function RichTextEditor(
  { value, onChange, templateUuid, resolveTemplateUuid, error },
  ref,
) {
  const editorRef = useRef<HTMLDivElement>(null);
  const sourceRef = useRef<HTMLTextAreaElement>(null);
  const savedRangeRef = useRef<Range | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const [textStyle, setTextStyle] = useState("p");
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [mergeVariable, setMergeVariable] = useState("");
  const [mergeError, setMergeError] = useState<string | null>(null);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkError, setLinkError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [imageDialogOpen, setImageDialogOpen] = useState(false);
  const [imageUploading, setImageUploading] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [sourceMode, setSourceMode] = useState(false);

  useEffect(() => {
    if (!sourceMode && editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value;
    }
  }, [sourceMode, value]);

  const captureSelection = () => {
    const editor = editorRef.current;
    const selection = window.getSelection();
    if (!editor || !selection || selection.rangeCount === 0) return;
    const range = selection.getRangeAt(0);
    if (editor.contains(range.commonAncestorContainer)) {
      savedRangeRef.current = range.cloneRange();
    }
  };

  const restoreSelection = () => {
    const editor = editorRef.current;
    if (!editor) return false;
    editor.focus({ preventScroll: true });
    const selection = window.getSelection();
    if (!selection) return false;

    let range = savedRangeRef.current;
    if (!range || !range.commonAncestorContainer.isConnected || !editor.contains(range.commonAncestorContainer)) {
      range = document.createRange();
      range.selectNodeContents(editor);
      range.collapse(false);
    }
    selection.removeAllRanges();
    selection.addRange(range);
    return true;
  };

  const syncEditor = () => {
    const html = editorRef.current?.innerHTML ?? "";
    onChange(html);
    captureSelection();
  };

  const runCommand = (command: string, argument?: string) => {
    if (sourceMode || !restoreSelection()) return;
    document.execCommand(command, false, argument);
    syncEditor();
  };

  const insertMergeVariableAtCursor = (variable: string) => {
    const normalized = variable.trim().replace(/^\{\{\s*|\s*\}\}$/g, "");
    if (!normalized) return;
    if (sourceMode && sourceRef.current) {
      const textarea = sourceRef.current;
      const token = `{{${normalized}}}`;
      const start = textarea.selectionStart ?? value.length;
      const end = textarea.selectionEnd ?? start;
      const next = `${value.slice(0, start)}${token}${value.slice(end)}`;
      onChange(next);
      window.requestAnimationFrame(() => {
        textarea.focus();
        textarea.setSelectionRange(start + token.length, start + token.length);
      });
      return;
    }
    runCommand("insertText", `{{${normalized}}}`);
  };

  useImperativeHandle(ref, () => ({
    insertMergeVariable: insertMergeVariableAtCursor,
  }));

  const insertMergeVariable = () => {
    const variable = mergeVariable.trim();
    if (!/^[A-Za-z_][A-Za-z0-9_.]*$/.test(variable)) {
      setMergeError("Use a variable name such as first_name or company.name.");
      return;
    }
    insertMergeVariableAtCursor(variable);
    setMergeVariable("");
    setMergeError(null);
    setMergeDialogOpen(false);
  };

  const addLink = () => {
    const url = linkUrl.trim();
    if (!isSafeHttpUrl(url)) {
      setLinkError("Enter a valid http:// or https:// URL.");
      return;
    }
    runCommand("createLink", url);
    setLinkUrl("");
    setLinkError(null);
    setLinkDialogOpen(false);
  };

  const insertImageUrl = async () => {
    const url = imageUrl.trim();
    if (!isSafeHttpUrl(url, true)) {
      setImageError("Enter a valid public HTTPS image URL.");
      return;
    }
    setImageError(null);
    try {
      await verifyRemoteImage(url);
    } catch {
      setImageError("This URL did not load a valid image. Use a direct public HTTPS image URL.");
      return;
    }
    runCommand("insertImage", url);
    setImageUrl("");
    setImageError(null);
    setImageDialogOpen(false);
  };

  const uploadImage = async (file?: File) => {
    if (!file) return;
    const allowedTypes = new Set(["image/png", "image/jpeg", "image/gif", "image/webp"]);
    if (!allowedTypes.has(file.type)) {
      setImageError("Choose a PNG, JPEG, GIF, or WebP image.");
      return;
    }
    if (file.size === 0 || file.size > 5 * 1024 * 1024) {
      setImageError("Image must be non-empty and 5 MB or smaller.");
      return;
    }

    setImageUploading(true);
    setImageError(null);
    try {
      const resolvedUuid = templateUuid ?? (resolveTemplateUuid ? await resolveTemplateUuid() : null);
      if (!resolvedUuid) {
        setImageError("Complete the required template fields before uploading an image.");
        return;
      }
      const asset = await uploadTemplateImage(resolvedUuid, file);
      runCommand("insertImage", asset.file_url);
    } catch (uploadError) {
      setImageError(getApiErrorMessage(uploadError, "Image could not be uploaded."));
    } finally {
      setImageUploading(false);
      if (imageInputRef.current) imageInputRef.current.value = "";
    }
  };

  const rememberCursorAnd = (action: () => void) => {
    captureSelection();
    action();
  };

  return (
    <>
      <TextPromptDialog
        open={mergeDialogOpen}
        onOpenChange={(open) => { setMergeDialogOpen(open); if (!open) setMergeError(null); }}
        title="Insert merge tag"
        description="Use the variable name only. MailTracko will wrap it in double braces."
        label="Merge variable"
        value={mergeVariable}
        onValueChange={(next) => { setMergeVariable(next); setMergeError(null); }}
        onSubmit={insertMergeVariable}
        placeholder="first_name"
        submitLabel="Insert tag"
        error={mergeError}
        maxLength={64}
      />
      <TextPromptDialog
        open={linkDialogOpen}
        onOpenChange={(open) => { setLinkDialogOpen(open); if (!open) setLinkError(null); }}
        title="Add link"
        description="Enter the destination URL for the selected text."
        label="Link URL"
        value={linkUrl}
        onValueChange={(next) => { setLinkUrl(next); setLinkError(null); }}
        onSubmit={addLink}
        placeholder="https://example.com"
        inputType="url"
        submitLabel="Add link"
        error={linkError}
        maxLength={2048}
      />
      <TextPromptDialog
        open={imageDialogOpen}
        onOpenChange={(open) => { setImageDialogOpen(open); if (!open) setImageError(null); }}
        title="Insert image from URL"
        description="Enter a public HTTPS image URL."
        label="Image URL"
        value={imageUrl}
        onValueChange={(next) => { setImageUrl(next); setImageError(null); }}
        onSubmit={insertImageUrl}
        placeholder="https://example.com/logo.png"
        inputType="url"
        submitLabel="Insert image"
        error={imageDialogOpen ? imageError : null}
        maxLength={2048}
      />

      <div className={`min-w-0 overflow-hidden rounded-xl border bg-white transition ${error ? "border-red-400" : "border-[#DDD5C3] focus-within:border-[#A88916] focus-within:ring-1 focus-within:ring-[#E9DFAE]/60"}`}>
        <div className="flex min-w-0 flex-wrap items-center gap-1 border-b border-[#EEE8D9] bg-[#FCFBF7] p-2">
          <AppSelect
            value={textStyle}
            onValueChange={(next) => {
              setTextStyle(next);
              runCommand("formatBlock", next);
            }}
            ariaLabel="Text style"
            options={[
              { value: "p", label: "Paragraph" },
              { value: "h2", label: "Heading" },
              { value: "h3", label: "Subheading" },
            ]}
            className="w-36"
            triggerClassName="min-h-8 py-1.5 text-xs"
          />
          {commands.map(({ label, command, icon: Icon }) => (
            <button
              key={command}
              type="button"
              onMouseDown={(event) => { event.preventDefault(); captureSelection(); runCommand(command); }}
              title={label}
              className="rounded-lg p-2 text-[#544F43] hover:bg-[#F2ECD9]"
              disabled={sourceMode}
            >
              <Icon className="h-4 w-4" />
            </button>
          ))}
          <button type="button" onClick={() => rememberCursorAnd(() => setLinkDialogOpen(true))} title="Add link" className="rounded-lg p-2 text-[#544F43] hover:bg-[#F2ECD9]" disabled={sourceMode}>
            <Link className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => rememberCursorAnd(() => setImageDialogOpen(true))} title="Insert image URL" className="rounded-lg p-2 text-[#544F43] hover:bg-[#F2ECD9]" disabled={sourceMode}>
            <ImagePlus className="h-4 w-4" />
          </button>
          <input
            ref={imageInputRef}
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            className="hidden"
            onChange={(event) => void uploadImage(event.target.files?.[0])}
          />
          <button
            type="button"
            disabled={imageUploading || sourceMode}
            onClick={() => { captureSelection(); imageInputRef.current?.click(); }}
            title="Upload and insert image"
            className="rounded-lg border border-[#D7C98F] px-2.5 py-1.5 text-xs font-medium text-[#725C0A] hover:bg-[#F8EDC5] disabled:cursor-not-allowed disabled:opacity-45"
          >
            {imageUploading ? "Uploading…" : "Upload image"}
          </button>
          <button type="button" onClick={() => rememberCursorAnd(() => setMergeDialogOpen(true))} className="ml-1 rounded-lg border border-[#D7C98F] bg-[#FFF9E5] px-2.5 py-1.5 text-xs font-medium text-[#725C0A] hover:bg-[#F8EDC5]">
            {"{}"} Merge tag
          </button>
          <div className="ml-auto flex items-center gap-1">
            <button type="button" onMouseDown={(event) => { event.preventDefault(); captureSelection(); runCommand("undo"); }} title="Undo" className="rounded-lg p-2 text-[#6E685A] hover:bg-[#F2ECD9]" disabled={sourceMode}><Undo2 className="h-4 w-4" /></button>
            <button type="button" onMouseDown={(event) => { event.preventDefault(); captureSelection(); runCommand("redo"); }} title="Redo" className="rounded-lg p-2 text-[#6E685A] hover:bg-[#F2ECD9]" disabled={sourceMode}><Redo2 className="h-4 w-4" /></button>
            <button
              type="button"
              onClick={() => setSourceMode((current) => !current)}
              aria-pressed={sourceMode}
              title={sourceMode ? "Return to visual editor" : "Edit HTML source"}
              className={`rounded-lg p-2 ${sourceMode ? "bg-[#F8EDC5] text-[#725C0A]" : "text-[#968E79] hover:bg-[#F2ECD9]"}`}
            >
              <Code2 className="h-4 w-4" />
            </button>
          </div>
        </div>
        {!imageDialogOpen && imageError ? <p role="alert" className="border-b border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">{imageError}</p> : null}
        {sourceMode ? (
          <textarea
            ref={sourceRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            spellCheck={false}
            aria-label="Template HTML source"
            className="min-h-[340px] w-full resize-y bg-white px-5 py-4 font-mono text-sm leading-6 text-[#1F2937] outline-none"
          />
        ) : (
          <div
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            onInput={syncEditor}
            onMouseUp={captureSelection}
            onKeyUp={captureSelection}
            onFocus={captureSelection}
            className="min-h-[340px] min-w-0 overflow-x-auto break-words px-5 py-4 text-sm leading-7 text-[#1F2937] outline-none [&_a]:break-all [&_a]:text-[#7A6208] [&_a]:underline [&_h2]:mb-3 [&_h2]:text-2xl [&_h2]:font-bold [&_h3]:mb-2 [&_h3]:text-lg [&_h3]:font-semibold [&_img]:h-auto [&_img]:max-w-full [&_ol]:list-decimal [&_ol]:pl-6 [&_p]:mb-3 [&_pre]:whitespace-pre-wrap [&_ul]:list-disc [&_ul]:pl-6"
          />
        )}
      </div>
      {error ? <p role="alert" className="mt-1.5 text-xs font-medium text-red-600">{error}</p> : null}
    </>
  );
});
