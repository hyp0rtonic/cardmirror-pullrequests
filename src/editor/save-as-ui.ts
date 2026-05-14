/**
 * Save As modal. Promise-based — resolves with the user's chosen
 * filename (and, eventually, additional export options) or `null` if
 * they cancelled. Replaces the old `window.prompt` flow which had no
 * room for options beyond the filename.
 *
 * Constructed per-call rather than as a singleton: a Promise per
 * invocation keeps the call-resolve coupling clean. Lifetime is
 * "open → user decides → resolve and remove."
 *
 * Options surface deliberately empty for now — the structure lives
 * inside `.pmd-save-as-options`, so future toggles slot in without
 * revisiting the shell.
 */

export interface SaveAsResult {
  filename: string;
  // Future per-export options land here (comments-anonymization,
  // page-break policy, etc.). Keeping the interface concrete rather
  // than `Record<string, unknown>` so callers get compile-time errors
  // when the option set widens.
}

export function openSaveAs(initialFilename: string): Promise<SaveAsResult | null> {
  return new Promise((resolve) => {
    new SaveAsModal(initialFilename, resolve);
  });
}

class SaveAsModal {
  private readonly overlay: HTMLDivElement;
  private readonly dialog: HTMLDivElement;
  private filenameInput!: HTMLInputElement;
  private settled = false;

  constructor(
    private readonly initialFilename: string,
    private readonly settle: (r: SaveAsResult | null) => void,
  ) {
    this.overlay = document.createElement('div');
    this.overlay.className = 'pmd-save-as-overlay';

    this.dialog = document.createElement('div');
    this.dialog.className = 'pmd-save-as-dialog';
    this.overlay.appendChild(this.dialog);

    this.overlay.addEventListener('click', (e) => {
      // Click on the dimmed backdrop cancels — matches the existing
      // reference and settings modals.
      if (e.target === this.overlay) this.cancel();
    });

    document.addEventListener('keydown', this.handleKey);

    this.render();
    document.body.appendChild(this.overlay);

    // Defer focus so the input renders before we put the cursor in it.
    requestAnimationFrame(() => {
      this.filenameInput.focus();
      this.filenameInput.select();
    });
  }

  private readonly handleKey = (e: KeyboardEvent): void => {
    if (this.settled) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      this.cancel();
    }
  };

  private render(): void {
    const header = document.createElement('header');
    header.className = 'pmd-save-as-header';
    const title = document.createElement('h2');
    title.textContent = 'Save As';
    header.appendChild(title);
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'pmd-save-as-close';
    closeBtn.textContent = '×';
    closeBtn.title = 'Cancel';
    closeBtn.addEventListener('click', () => this.cancel());
    header.appendChild(closeBtn);
    this.dialog.appendChild(header);

    const form = document.createElement('form');
    form.className = 'pmd-save-as-body';
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.confirm();
    });

    const fileLabel = document.createElement('label');
    fileLabel.className = 'pmd-save-as-field';
    const fileSpan = document.createElement('span');
    fileSpan.className = 'pmd-save-as-field-label';
    fileSpan.textContent = 'File name';
    fileLabel.appendChild(fileSpan);
    this.filenameInput = document.createElement('input');
    this.filenameInput.type = 'text';
    this.filenameInput.className = 'pmd-save-as-input';
    this.filenameInput.value = this.initialFilename;
    this.filenameInput.spellcheck = false;
    this.filenameInput.autocomplete = 'off';
    fileLabel.appendChild(this.filenameInput);
    form.appendChild(fileLabel);

    // Empty options container — placeholder for the round of features
    // that prompted this dialog. Renders nothing until populated, so
    // the dialog stays tight today.
    const options = document.createElement('div');
    options.className = 'pmd-save-as-options';
    form.appendChild(options);

    const footer = document.createElement('footer');
    footer.className = 'pmd-save-as-footer';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'pmd-save-as-btn pmd-save-as-btn-secondary';
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', () => this.cancel());
    footer.appendChild(cancel);
    const save = document.createElement('button');
    save.type = 'submit';
    save.className = 'pmd-save-as-btn pmd-save-as-btn-primary';
    save.textContent = 'Save';
    footer.appendChild(save);
    form.appendChild(footer);

    this.dialog.appendChild(form);
  }

  private confirm(): void {
    const trimmed = this.filenameInput.value.trim();
    if (!trimmed) return; // Refuse empty; user has to type something.
    const filename = trimmed.toLowerCase().endsWith('.docx')
      ? trimmed
      : `${trimmed}.docx`;
    this.finish({ filename });
  }

  private cancel(): void {
    this.finish(null);
  }

  private finish(result: SaveAsResult | null): void {
    if (this.settled) return;
    this.settled = true;
    document.removeEventListener('keydown', this.handleKey);
    this.overlay.remove();
    this.settle(result);
  }
}
