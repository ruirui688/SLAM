# P244 Remote Independent Dynamic-Label Annotation Bundle

## Purpose

`paper/export/independent_dynamic_label_remote_p244.html` is a self-contained annotation page that can be sent to a remote reviewer. Unlike the P243 local web tool, this file embeds all 72 review images as compressed JPEG data URIs and does not require access to the repository `outputs/` directory.

## Bundle Size

- Samples: 18
- Embedded images: 72
- JPEG max width: 1000 px
- JPEG quality: 76
- Encoded image bytes before base64: 4,769,941
- Final HTML size: 6,404,327 bytes (6.11 MiB)

## How To Use

1. Send `paper/export/independent_dynamic_label_remote_p244.html` directly to the reviewer.
2. The reviewer opens it in a browser. No server, CDN, or local image folder is required.
3. The browser stores progress in `localStorage` on that machine.
4. The reviewer exports the filled CSV or JSON and sends the exported labels back.
5. Audit the returned CSV with `tools/audit_interactive_dynamic_labels_p243.py <exported.csv>` before using it for any claim-boundary decision.

## Boundary

This is not a public URL or hosted release. It is a sendable local HTML bundle. Model overlays remain context only, not ground truth. Reviewers must not inspect admission labels while labeling. P195 remains `BLOCKED` until non-empty exported labels pass coverage, conflict, and independence audit.
