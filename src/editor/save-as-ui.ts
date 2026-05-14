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
  /** Include comments in the saved doc. No-op until comments-import
   *  lands; reserved here so the dialog UI exists alongside the
   *  comments work. */
  includeComments: boolean;
  /** Include analytic content. When false, doc-level analytic_units
   *  drop entirely; in-card analytic paragraphs drop. */
  includeAnalytics: boolean;
  /** Include undertag paragraphs (doc-level and inside cards /
   *  analytic_units). */
  includeUndertags: boolean;
  /** Save what's visible in read mode: headings, tags, in-card
   *  analytics, cite-marked text inside cite_paragraphs, highlighted
   *  text inside body paragraphs. Mutually exclusive with the three
   *  include-* options above. */
  readMode: boolean;
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
  private commentsBox!: HTMLInputElement;
  private analyticsBox!: HTMLInputElement;
  private undertagsBox!: HTMLInputElement;
  private readModeBox!: HTMLInputElement;
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

    // Options: four checkboxes governing what the exporter includes.
    // Read Mode is mutually exclusive with the other three — checking
    // it disables and unchecks the include-* group; checking any of
    // those three disables Read Mode.
    const options = document.createElement('div');
    options.className = 'pmd-save-as-options';
    options.appendChild(this.buildOptionsHeading());

    this.commentsBox = this.buildCheckbox('Include comments', true);
    this.analyticsBox = this.buildCheckbox('Include analytics', true);
    this.undertagsBox = this.buildCheckbox('Include undertags', true);
    this.readModeBox = this.buildCheckbox('Read mode (only headings, tags, analytics, cites, highlights)', false);

    options.appendChild(this.commentsBox.parentElement!);
    options.appendChild(this.analyticsBox.parentElement!);
    options.appendChild(this.undertagsBox.parentElement!);
    options.appendChild(this.readModeBox.parentElement!);

    const groupedIncludes = [this.commentsBox, this.analyticsBox, this.undertagsBox];
    const refreshGroupState = (): void => {
      const readMode = this.readModeBox.checked;
      for (const box of groupedIncludes) {
        box.disabled = readMode;
        const label = box.parentElement as HTMLLabelElement;
        label.classList.toggle('pmd-save-as-option-disabled', readMode);
      }
    };
    this.readModeBox.addEventListener('change', () => {
      if (this.readModeBox.checked) {
        // Mutual exclusion: turning on read mode clears + locks the
        // include-* checkboxes (their values won't ship in the result
        // either way, but reflecting it visually avoids confusion).
        for (const box of groupedIncludes) box.checked = false;
      }
      refreshGroupState();
    });
    for (const box of groupedIncludes) {
      box.addEventListener('change', () => {
        if (box.checked) {
          this.readModeBox.checked = false;
          refreshGroupState();
        }
      });
    }

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

  private buildOptionsHeading(): HTMLElement {
    const h = document.createElement('div');
    h.className = 'pmd-save-as-options-heading';
    h.textContent = 'Include';
    return h;
  }

  private buildCheckbox(labelText: string, defaultChecked: boolean): HTMLInputElement {
    const label = document.createElement('label');
    label.className = 'pmd-save-as-option';
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = defaultChecked;
    label.appendChild(box);
    const text = document.createElement('span');
    text.textContent = labelText;
    label.appendChild(text);
    return box;
  }

  private confirm(): void {
    const trimmed = this.filenameInput.value.trim();
    if (!trimmed) return; // Refuse empty; user has to type something.
    const filename = trimmed.toLowerCase().endsWith('.docx')
      ? trimmed
      : `${trimmed}.docx`;
    const readMode = this.readModeBox.checked;
    this.finish({
      filename,
      // The include-* values are forced to false in read-mode so the
      // result object is self-consistent — even though the read-mode
      // transform doesn't read them.
      includeComments: readMode ? false : this.commentsBox.checked,
      includeAnalytics: readMode ? false : this.analyticsBox.checked,
      includeUndertags: readMode ? false : this.undertagsBox.checked,
      readMode,
    });
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
