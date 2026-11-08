/**
 * Client-side image preparation for the purchase photo step.
 *
 * Phone cameras produce 3–12 MB photos, but the API is reached through a Vercel
 * Function, and Vercel rejects request bodies over 4.5 MB with
 * `413 FUNCTION_PAYLOAD_TOO_LARGE`. So the photo is re-encoded in the browser
 * first: scale the long edge down, then step the JPEG quality down until the
 * file fits under {@link MAX_UPLOAD_BYTES}.
 */

/** Vercel Functions refuse bodies over 4.5 MB; leave room for the form fields. */
export const MAX_UPLOAD_BYTES = 3.5 * 1024 * 1024;

/** Longest edge after scaling — plenty of detail to read a price tag. */
const MAX_EDGE = 1600;

/** JPEG qualities tried, best first, until the encoded file fits. */
const QUALITY_STEPS = [0.85, 0.72, 0.6, 0.5, 0.4];

/** Image types the browser can decode and re-encode reliably. */
const REENCODABLE_TYPES = new Set(["image/jpeg", "image/jpg", "image/png", "image/webp"]);

type DecodedImage = ImageBitmap | HTMLImageElement;

function isReencodable(file: File): boolean {
  // HEIC/HEIF (iPhone default) is decoded by Safari but not by Chrome's canvas.
  // Those are sent as picked and rely on the API's own 10 MB ceiling instead.
  return REENCODABLE_TYPES.has(file.type.toLowerCase());
}

async function decode(file: File): Promise<DecodedImage> {
  if (typeof createImageBitmap === "function") {
    try {
      return await createImageBitmap(file);
    } catch {
      // Fall through to the <img> path (older Safari, unusual colour profiles).
    }
  }

  const url = URL.createObjectURL(file);
  try {
    return await new Promise<HTMLImageElement>((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("That image could not be read."));
      image.src = url;
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

function toJpegBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
}

function asUploadFile(blob: Blob, original: File): File {
  const base = original.name.replace(/\.[^.]+$/, "") || "purchase";
  return new File([blob], `${base}.jpg`, {
    type: "image/jpeg",
    lastModified: Date.now(),
  });
}

/**
 * Return a file that fits the upload limit, or the original when there is
 * nothing to gain (already small, HEIC, or undecodable). Best effort: a photo
 * that cannot be squeezed under the cap is returned as small as we could make
 * it, and the API answers with its own error if that still fails.
 */
export async function prepareImageForUpload(file: File): Promise<File> {
  if (file.size <= MAX_UPLOAD_BYTES || !isReencodable(file)) return file;

  let source: DecodedImage;
  try {
    source = await decode(file);
  } catch {
    return file;
  }

  try {
    const longestEdge = Math.max(source.width, source.height);
    const scale = longestEdge > MAX_EDGE ? MAX_EDGE / longestEdge : 1;
    const width = Math.max(1, Math.round(source.width * scale));
    const height = Math.max(1, Math.round(source.height * scale));

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");
    if (!context) return file;

    // JPEG has no alpha channel: flatten onto white so PNGs don't go black.
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, width, height);
    context.drawImage(source, 0, 0, width, height);

    let candidate: Blob | null = null;
    for (const quality of QUALITY_STEPS) {
      candidate = await toJpegBlob(canvas, quality);
      if (candidate && candidate.size <= MAX_UPLOAD_BYTES) break;
    }

    if (!candidate) return file;
    return candidate.size < file.size ? asUploadFile(candidate, file) : file;
  } finally {
    if ("close" in source) source.close();
  }
}
