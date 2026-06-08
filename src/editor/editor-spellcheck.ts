/**
 * Editor spellcheck application.
 *
 * Setting the `spellcheck` attribute on the editable is necessary but
 * NOT sufficient: Chromium only (re)evaluates an editing host's
 * spellcheck state when the host gains focus, and ignores an attribute
 * flip on the live, already-focused host. The setting toggle lives in
 * the Settings dialog, so the editor is blurred when the value changes
 * — which is exactly the case where a bare `setAttribute` appears to do
 * nothing. So after ENABLING we force Chromium to re-scan by bouncing
 * focus: immediately if the view is focused, otherwise once the next
 * time it gains focus (e.g. when the user clicks back into the editor).
 * ProseMirror restores its own selection on `focus()`, so the cursor is
 * preserved and the bounce is imperceptible.
 */
import type { EditorView } from 'prosemirror-view';

/** Property flag stashed on the editable so repeated toggles while the
 *  editor is blurred don't stack multiple one-shot focus listeners. */
const ARMED = '__pmdSpellcheckArmed';

type ArmableDom = HTMLElement & { [ARMED]?: boolean };

export function applySpellcheckToView(view: EditorView, enabled: boolean): void {
  const dom = view.dom as ArmableDom;
  dom.setAttribute('spellcheck', enabled ? 'true' : 'false');
  // Disabling takes effect without a re-scan — Chromium drops the
  // squiggles on the next paint. Only enabling needs the focus bounce.
  if (!enabled) return;
  if (view.hasFocus()) {
    retriggerSpellcheckScan(view);
  } else if (!dom[ARMED]) {
    dom[ARMED] = true;
    const onFocus = (): void => {
      dom[ARMED] = false;
      dom.removeEventListener('focus', onFocus);
      // Let the genuine focus settle before bouncing it.
      requestAnimationFrame(() => {
        if (view.hasFocus()) retriggerSpellcheckScan(view);
      });
    };
    dom.addEventListener('focus', onFocus);
  }
}

function retriggerSpellcheckScan(view: EditorView): void {
  view.dom.blur();
  view.focus();
}
