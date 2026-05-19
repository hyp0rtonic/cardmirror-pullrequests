/**
 * `Element.scrollIntoView` with cv:auto-aware corrections.
 *
 * Cards (`.pmd-card`, `.pmd-pocket`, `.pmd-hat`, `.pmd-block`,
 * `.pmd-analytic-unit`) carry `content-visibility: auto` with a
 * `contain-intrinsic-size: auto <small length>` fallback. Off-screen
 * subtrees skip layout and the browser substitutes the placeholder
 * height for any scroll-position math. A plain `scrollIntoView` on
 * a deep heading therefore lands tens of pixels off per never-
 * rendered card above the target.
 *
 * Fix shape:
 *   1. Add `pmd-force-materialize` to the editor's DOM — a class
 *      whose CSS rule flips every cv:auto card / heading to
 *      `content-visibility: visible !important`. The browser must
 *      now lay out real content for every card rather than using
 *      `contain-intrinsic-size` placeholders.
 *   2. Read `editor.offsetHeight` to force a synchronous layout
 *      flush so the cv:visible override is reflected in the layout
 *      tree before any scroll math runs. This is the expensive
 *      step on big docs — a full-doc layout pass, typically
 *      200–500 ms on a 2000-card Verbatim. The user sees this
 *      as a slight pause on every click.
 *   3. Call `scrollIntoView(block)`. With real heights everywhere,
 *      the browser's alignment math is accurate on the first try.
 *   4. Iterate: re-measure the target's position; if the previous
 *      iteration changed it, call `scrollIntoView` again and check
 *      stability on the next frame. Converges when two consecutive
 *      iterations produce the same position. The class stays on
 *      through the entire iteration so cv:auto can't kick back in
 *      mid-loop and shift things again.
 *   5. Remove the class. cv:auto resumes; cards off-screen at this
 *      point use their placeholder sizes again. The target is
 *      on-screen and its card stays materialized regardless.
 *
 * This is the "accurate but pause on every click" trade-off. We
 * tried four alternatives to avoid the pause and rolled them all
 * back (see the closed item in WISHLIST.md for the full account).
 * The pause is the price for precision until one of the queued
 * follow-ups (sync-warm path, persist registry to `.cmir`, etc.)
 * lands.
 *
 * Editing performance is preserved because the class is removed
 * at the end of the refine loop — every keystroke between scrolls
 * sees cv:auto in effect, which is responsible for a meaningful
 * share of per-keystroke layout cost on long docs (commit
 * `314944a`).
 */

import type { EditorView } from 'prosemirror-view';

/** Max iterations for the refine loop. Convergence in 1-2 is
 *  the norm with force-materialize active; this cap defends
 *  against pathological cases where layout never settles. */
const MAX_REFINE_ITERATIONS = 5;

/** Convergence tolerance in CSS pixels. */
const REFINE_TOLERANCE_PX = 1;

export type PreciseScrollBlock = 'start' | 'center';

export function preciseScrollIntoView(
  view: EditorView,
  target: HTMLElement,
  block: PreciseScrollBlock = 'start',
): void {
  if (!target.isConnected) return;

  const editor = view.dom as HTMLElement;
  editor.classList.add('pmd-force-materialize');
  // Force a synchronous layout pass with the cv:visible override
  // applied. Without this read, the upcoming scrollIntoView could
  // see the pre-class-add layout (cv:auto placeholders).
  void editor.offsetHeight;
  // Coarse scroll. With cv:visible everywhere, the browser's
  // alignment math runs against real heights.
  target.scrollIntoView({ behavior: 'auto', block });

  // Refinement: a few frames of "did the target's screen position
  // stop moving?" If yes, we're done. If not, scrollIntoView again
  // and check next frame. Converges when two consecutive samples
  // are equal (within tolerance).
  let iterations = 0;
  let prevTop = Number.POSITIVE_INFINITY;

  const refine = (): void => {
    if (!target.isConnected) {
      editor.classList.remove('pmd-force-materialize');
      return;
    }
    const rect = target.getBoundingClientRect();
    const stable = Math.abs(rect.top - prevTop) < REFINE_TOLERANCE_PX;
    if (stable || iterations >= MAX_REFINE_ITERATIONS) {
      // Done — release the cv:visible override so cv:auto resumes
      // skipping off-screen content. Preserves the editing-hot-
      // path layout cost.
      editor.classList.remove('pmd-force-materialize');
      return;
    }
    prevTop = rect.top;
    iterations++;
    // Re-issue scrollIntoView with the same alignment. With
    // cv:visible still in effect, this uses the same real-height
    // layout as the previous call; any difference in result
    // reflects late layout work the previous frame, which the
    // next sample catches.
    target.scrollIntoView({ behavior: 'auto', block });
    requestAnimationFrame(refine);
  };
  requestAnimationFrame(refine);
}
