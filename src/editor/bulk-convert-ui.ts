/**
 * Bulk convert — a home-screen utility to batch-convert between
 * `.docx` and `.cmir`.
 *
 * Pick a single file or a folder (recursed, incl. subfolders); convert
 * in the chosen direction; output either next to each original (same
 * location, swapped extension) or bundled into a single `.zip`.
 *
 * Electron-only: it needs recursive directory listing + write-to-path,
 * so the home screen only surfaces the entry on the desktop edition.
 */

import JSZip from 'jszip';
import { fromDocxFull, parseNative, serializeNative, toDocx } from '../index.js';
import { getHost, getElectronHost } from './host/index.js';

type Direction = 'docx2cmir' | 'cmir2docx';
type Output = 'inplace' | 'zip';

/** Convert one file's bytes in the given direction, preserving
 *  comment threads. */
async function convertBytes(bytes: Uint8Array, dir: Direction): Promise<Uint8Array> {
  if (dir === 'docx2cmir') {
    const { doc, threads } = await fromDocxFull(bytes);
    return serializeNative(doc, threads.length ? { threads } : undefined);
  }
  const { doc, threads } = parseNative(bytes);
  return toDocx(doc, threads.length ? { threads } : undefined);
}

function swapExt(p: string, dir: Direction): string {
  return dir === 'docx2cmir'
    ? p.replace(/\.docx$/i, '.cmir')
    : p.replace(/\.cmir$/i, '.docx');
}

class BulkConvertModal {
  private readonly overlay: HTMLDivElement;
  private readonly dialog: HTMLDivElement;
  private statusEl!: HTMLDivElement;
  private busy = false;
  private settled = false;
  private dirRadios!: Record<Direction, HTMLInputElement>;
  private outRadios!: Record<Output, HTMLInputElement>;

  constructor() {
    this.overlay = document.createElement('div');
    this.overlay.className = 'pmd-bulk-overlay';
    this.dialog = document.createElement('div');
    this.dialog.className = 'pmd-bulk-dialog';
    this.overlay.appendChild(this.dialog);
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.close();
    });
    document.addEventListener('keydown', this.onKey, true);
    this.render();
    document.body.appendChild(this.overlay);
  }

  private onKey = (e: KeyboardEvent): void => {
    if (e.key === 'Escape' && !this.busy) {
      e.preventDefault();
      this.close();
    }
  };

  private close(): void {
    if (this.settled || this.busy) return;
    this.settled = true;
    document.removeEventListener('keydown', this.onKey, true);
    this.overlay.remove();
  }

  private direction(): Direction {
    return this.dirRadios.cmir2docx.checked ? 'cmir2docx' : 'docx2cmir';
  }
  private output(): Output {
    return this.outRadios.zip.checked ? 'zip' : 'inplace';
  }

  private render(): void {
    const header = document.createElement('header');
    header.className = 'pmd-bulk-header';
    const h = document.createElement('h2');
    h.textContent = 'Bulk convert';
    header.appendChild(h);
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'pmd-bulk-close';
    close.textContent = '×';
    close.title = 'Close';
    close.addEventListener('click', () => this.close());
    header.appendChild(close);
    this.dialog.appendChild(header);

    const body = document.createElement('div');
    body.className = 'pmd-bulk-body';

    this.dirRadios = {
      docx2cmir: radio('pmd-bulk-dir', '.docx → .cmir', true),
      cmir2docx: radio('pmd-bulk-dir', '.cmir → .docx', false),
    };
    body.appendChild(
      fieldset('Direction', [this.dirRadios.docx2cmir, this.dirRadios.cmir2docx]),
    );

    this.outRadios = {
      inplace: radio('pmd-bulk-out', 'Save next to each original', true),
      zip: radio('pmd-bulk-out', 'Save as a single .zip', false),
    };
    body.appendChild(fieldset('Output', [this.outRadios.inplace, this.outRadios.zip]));

    const actions = document.createElement('div');
    actions.className = 'pmd-bulk-actions';
    const fileBtn = button('Choose file…', () => void this.runFile());
    const folderBtn = button('Choose folder…', () => void this.runFolder());
    actions.append(fileBtn, folderBtn);
    body.appendChild(actions);

    this.statusEl = document.createElement('div');
    this.statusEl.className = 'pmd-bulk-status';
    body.appendChild(this.statusEl);

    this.dialog.appendChild(body);
  }

  private setStatus(msg: string): void {
    this.statusEl.textContent = msg;
  }

  private setBusy(on: boolean): void {
    this.busy = on;
    this.dialog.classList.toggle('pmd-bulk-busy', on);
  }

  // ── Runs ──────────────────────────────────────────────────────────

  private async runFile(): Promise<void> {
    if (this.busy) return;
    const dir = this.direction();
    const out = this.output();
    const srcExt = dir === 'docx2cmir' ? 'docx' : 'cmir';
    const opened = await getHost().openFile({
      filters: [{ name: `.${srcExt}`, extensions: [srcExt] }],
    });
    if (!opened) return;
    this.setBusy(true);
    this.setStatus(`Converting ${opened.name}…`);
    try {
      const converted = await convertBytes(opened.bytes, dir);
      if (out === 'zip') {
        await this.saveZip([{ name: swapExt(opened.name, dir), bytes: converted }]);
      } else {
        const electron = getElectronHost();
        if (typeof opened.handle !== 'string' || !electron) {
          throw new Error('In-place output requires the desktop edition.');
        }
        await electron.writeFileAtPath(swapExt(opened.handle, dir), converted);
      }
      this.setStatus(`Converted “${opened.name}”.`);
    } catch (err) {
      this.setStatus(`Failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      this.setBusy(false);
    }
  }

  private async runFolder(): Promise<void> {
    if (this.busy) return;
    const electron = getElectronHost();
    if (!electron) {
      this.setStatus('Folder conversion requires the desktop edition.');
      return;
    }
    const dir = this.direction();
    const out = this.output();
    const srcExt = dir === 'docx2cmir' ? 'docx' : 'cmir';
    const folder = await electron.pickDirectory({ title: 'Choose a folder to convert' });
    if (!folder) return;
    this.setBusy(true);
    this.setStatus('Scanning…');
    try {
      const files = await electron.listFilesRecursive(folder, srcExt);
      if (files.length === 0) {
        this.setStatus(`No .${srcExt} files found in that folder.`);
        return;
      }
      const zip = out === 'zip' ? new JSZip() : null;
      let ok = 0;
      let failed = 0;
      for (let i = 0; i < files.length; i++) {
        const f = files[i]!;
        this.setStatus(`Converting ${i + 1} / ${files.length}…`);
        try {
          const read = await electron.readFileAtPath(f.path);
          if (!read) throw new Error('unreadable');
          const converted = await convertBytes(read.bytes, dir);
          if (zip) {
            zip.file(swapExt(f.relPath, dir).replace(/\\/g, '/'), converted);
          } else {
            await electron.writeFileAtPath(swapExt(f.path, dir), converted);
          }
          ok++;
        } catch (err) {
          failed++;
          console.error('Bulk convert failed for', f.path, err);
        }
      }
      if (zip && ok > 0) {
        const blob = await zip.generateAsync({ type: 'uint8array' });
        await this.saveZip(null, blob);
      }
      this.setStatus(
        `Done — ${ok} converted${failed ? `, ${failed} failed (see console)` : ''}.`,
      );
    } catch (err) {
      this.setStatus(`Failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      this.setBusy(false);
    }
  }

  /** Save a zip — either built here from `entries`, or a pre-built
   *  `prebuilt` byte array. */
  private async saveZip(
    entries: Array<{ name: string; bytes: Uint8Array }> | null,
    prebuilt?: Uint8Array,
  ): Promise<void> {
    let bytes = prebuilt;
    if (!bytes) {
      const zip = new JSZip();
      for (const e of entries ?? []) zip.file(e.name, e.bytes);
      bytes = await zip.generateAsync({ type: 'uint8array' });
    }
    await getHost().saveAs('converted.zip', bytes, {
      filters: [{ name: 'Zip archive', extensions: ['zip'] }],
    });
  }
}

// ── Small DOM helpers ────────────────────────────────────────────────

function radio(name: string, label: string, checked: boolean): HTMLInputElement {
  const input = document.createElement('input');
  input.type = 'radio';
  input.name = name;
  input.checked = checked;
  // Stash the label so `fieldset` can wrap it.
  (input as HTMLInputElement & { _label?: string })._label = label;
  return input;
}

function fieldset(legend: string, radios: HTMLInputElement[]): HTMLElement {
  const wrap = document.createElement('div');
  wrap.className = 'pmd-bulk-field';
  const lg = document.createElement('div');
  lg.className = 'pmd-bulk-field-label';
  lg.textContent = legend;
  wrap.appendChild(lg);
  for (const input of radios) {
    const row = document.createElement('label');
    row.className = 'pmd-bulk-radio';
    const text = document.createElement('span');
    text.textContent = (input as HTMLInputElement & { _label?: string })._label ?? '';
    row.append(input, text);
    wrap.appendChild(row);
  }
  return wrap;
}

function button(label: string, onClick: () => void): HTMLButtonElement {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'pmd-bulk-btn';
  b.textContent = label;
  b.addEventListener('click', onClick);
  return b;
}

export function openBulkConvert(): void {
  new BulkConvertModal();
}
