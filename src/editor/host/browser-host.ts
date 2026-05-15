/**
 * BrowserHost — the Host implementation for the plain web edition
 * (and, by extension, the installable PWA). All file I/O goes
 * through web platform APIs: `<input type="file">` for opens,
 * `showSaveFilePicker` (Chromium) or a synthesized `<a download>`
 * link (everyone else) for saves.
 *
 * The hidden file-input that opens files is owned and recycled by
 * this class — callers don't see it. We allow only one open dialog
 * to be pending at a time (browsers serialize them anyway).
 */

import type { Host, OpenedFile, SaveResult } from './types.js';

/** Chrome's File System Access API is gated by feature detection;
 *  declare the shape we use so we don't have to `as unknown as` it
 *  everywhere. */
interface ShowSaveFilePickerOptions {
  suggestedName?: string;
  types?: { description: string; accept: Record<string, string[]> }[];
}
interface FileSystemFileHandle {
  name?: string;
  createWritable(): Promise<{
    write(data: Blob | ArrayBuffer | Uint8Array): Promise<void>;
    close(): Promise<void>;
  }>;
}
type ShowSaveFilePicker = (
  opts: ShowSaveFilePickerOptions,
) => Promise<FileSystemFileHandle>;

const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

export class BrowserHost implements Host {
  readonly kind = 'browser' as const;

  /** Lazily-created hidden file input. Reused across opens; on each
   *  open we set up a one-shot listener that resolves the pending
   *  promise. */
  private fileInput: HTMLInputElement | null = null;

  /** When a previous openFile() is mid-dialog, queue follow-up
   *  callers behind a chain so two near-simultaneous opens don't
   *  step on each other's event listeners. */
  private openInFlight: Promise<OpenedFile | null> = Promise.resolve(null);

  async openFile(): Promise<OpenedFile | null> {
    const next = this.openInFlight.then(() => this.openOnce());
    this.openInFlight = next.then(
      () => null,
      () => null,
    );
    return next;
  }

  private openOnce(): Promise<OpenedFile | null> {
    const input = this.ensureFileInput();
    return new Promise((resolve, reject) => {
      // Browser quirk: if the user picks the same filename twice in
      // a row, the second `change` event won't fire unless `.value`
      // is cleared. Reset every time to be safe.
      input.value = '';

      let settled = false;
      const onChange = async (): Promise<void> => {
        if (settled) return;
        settled = true;
        input.removeEventListener('change', onChange);
        window.removeEventListener('focus', onCancelMaybe);
        const file = input.files?.[0];
        if (!file) {
          resolve(null);
          return;
        }
        try {
          const buf = await file.arrayBuffer();
          resolve({
            name: file.name,
            bytes: new Uint8Array(buf),
          });
        } catch (err) {
          reject(err);
        }
      };

      // Cancellation has no native event in browsers — the user
      // closes the dialog and nothing fires. We use the trick of
      // listening for window `focus` (returns when the OS dialog
      // closes) plus a short tick to check if any file was picked.
      // If not, resolve null.
      const onCancelMaybe = (): void => {
        // The `change` event reliably fires BEFORE focus returns
        // when a file is picked, so a short defer is enough to
        // disambiguate. If `change` is going to fire it'll have
        // fired by the time this runs.
        window.setTimeout(() => {
          if (settled) return;
          if (!input.files || input.files.length === 0) {
            settled = true;
            input.removeEventListener('change', onChange);
            window.removeEventListener('focus', onCancelMaybe);
            resolve(null);
          }
        }, 200);
      };

      input.addEventListener('change', onChange);
      window.addEventListener('focus', onCancelMaybe, { once: true });
      input.click();
    });
  }

  async saveAs(
    suggestedName: string,
    bytes: Uint8Array,
  ): Promise<SaveResult | null> {
    // Copy into a regular ArrayBuffer so Blob's BlobPart contract
    // is happy. Some TypedArray backing buffers are SharedArrayBuffer
    // in worker contexts; Blob doesn't accept those directly.
    const ab = new ArrayBuffer(bytes.byteLength);
    new Uint8Array(ab).set(bytes);
    const blob = new Blob([ab], { type: DOCX_MIME });

    // Preferred path: File System Access API. Chromium-based
    // browsers (Chrome / Edge / Opera / Arc / Brave) give us a real
    // native save dialog with the suggested name pre-filled and
    // write straight to disk. We also get back a handle we can
    // later pass to an in-place Save (once that lands).
    const showSaveFilePicker = (window as unknown as {
      showSaveFilePicker?: ShowSaveFilePicker;
    }).showSaveFilePicker;

    if (typeof showSaveFilePicker === 'function') {
      let handle: FileSystemFileHandle;
      try {
        handle = await showSaveFilePicker({
          suggestedName,
          types: [
            {
              description: 'Word document',
              accept: { [DOCX_MIME]: ['.docx'] },
            },
          ],
        });
      } catch (e) {
        // AbortError = user cancelled the OS dialog. Quietly bail.
        if (e instanceof DOMException && e.name === 'AbortError') {
          return null;
        }
        throw e;
      }
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return {
        name: handle.name ?? suggestedName,
        handle,
      };
    }

    // Fallback: synthesize a download link. Safari, Firefox, mobile
    // browsers, anything without the File System Access API. The
    // user gets a download (no native save dialog with location
    // chooser, unless their browser is configured to prompt — most
    // aren't). We can't return a handle here because there's no
    // persistent reference to the saved location.
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = suggestedName;
    a.click();
    URL.revokeObjectURL(url);
    return { name: suggestedName };
  }

  private ensureFileInput(): HTMLInputElement {
    if (this.fileInput) return this.fileInput;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.docx';
    input.hidden = true;
    // Off-screen but not display:none — some browsers ignore .click()
    // on display:none inputs. `hidden` is the modern equivalent that
    // still lets click() work.
    document.body.appendChild(input);
    this.fileInput = input;
    return input;
  }
}
