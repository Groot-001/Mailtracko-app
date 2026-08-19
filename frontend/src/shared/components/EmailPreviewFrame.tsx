interface EmailPreviewFrameProps {
  html: string;
  title: string;
  className?: string;
}

const buildPreviewDocument = (html: string) => `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; background: #ffffff; }
      body {
        color: #28303e;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
        line-height: 1.7;
        overflow-wrap: anywhere;
        padding: 24px;
      }
      h1, h2, h3, h4, h5, h6 { color: #171a22; line-height: 1.25; margin: 0 0 16px; }
      p { margin: 0 0 16px; }
      ul, ol { margin: 0 0 16px; padding-left: 24px; }
      a { color: #7a6208; text-decoration: underline; }
      img, video, svg, canvas { display: block; height: auto; max-width: 100% !important; }
      pre, code { max-width: 100%; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; }
      body > * { max-width: 100% !important; }
      blockquote { border-left: 3px solid #d7c98f; margin: 0 0 16px; padding-left: 16px; }
      table { border-collapse: collapse; display: block; max-width: 100%; overflow-x: auto; width: 100%; }
      td, th { border: 1px solid #e8e1d0; padding: 8px; text-align: left; }
    </style>
  </head>
  <body>${html}</body>
</html>`;

export const EmailPreviewFrame = ({ html, title, className = "" }: EmailPreviewFrameProps) => (
  <iframe
    title={title}
    sandbox=""
    srcDoc={buildPreviewDocument(html)}
    className={`block w-full min-w-0 max-w-full border-0 bg-white ${className}`}
    loading="lazy"
    referrerPolicy="no-referrer"
    aria-label={title}
  />
);
