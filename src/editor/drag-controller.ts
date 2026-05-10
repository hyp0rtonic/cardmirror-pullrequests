/**
 * Workspace-scoped drag controller.
 *
 * Coordinates header drag-and-drop within the nav pane (Phase 1) and
 * — eventually — between the nav pane and the editor surface, and
 * between separate documents in a multi-doc workspace.
 *
 * Architecture: source(s) call `begin(session)` to start a drag.
 * Surfaces register pointer-hit handlers and tell the controller which
 * drop target the cursor is over via `setHoverTarget`. When the pointer
 * is released the active surface calls `commit()`; cancellation goes
 * through `cancel()`. Subscribers (nav pane, eventually the editor
 * view) listen for state changes to render drag visuals.
 *
 * For Phase 1 we support a single-item, same-view drop. Multi-item
 * (Phase 2) and cross-view (Phase 3) extend this without changing the
 * shape — `DragSession.items` is already plural.
 */

import type { EditorView } from 'prosemirror-view';
import type { EditorState, Transaction } from 'prosemirror-state';

export interface DragItem {
  /** Doc position range covering the dragged unit (heading + its
   *  subtree, or a card/analytic_unit container). */
  from: number;
  to: number;
  /** Stable heading id, when one exists. */
  id: string | null;
  /** Schema type name (pocket / hat / block / card / analytic_unit). */
  type: string;
  /** Outline level (1–4). */
  level: number;
  /** Display label for the pickup pill (the heading's text). */
  label: string;
}

export interface DragSession {
  /** The view the source content lives in. */
  view: EditorView;
  /** All items being dragged, in document order. */
  items: DragItem[];
}

export interface DropTarget {
  /** The view the drop should land in. (Same as session.view in
   *  Phase 1 — a future cross-doc commit can land in another view.) */
  view: EditorView;
  /** Document position to insert at, in the target view's current doc. */
  insertPos: number;
}

type DragEvent = 'begin' | 'move' | 'end';
type Listener = (event: DragEvent) => void;

class DragControllerImpl {
  private session: DragSession | null = null;
  private hoverTarget: DropTarget | null = null;
  private pointerX = 0;
  private pointerY = 0;
  private listeners: Set<Listener> = new Set();

  isActive(): boolean {
    return this.session !== null;
  }

  getSession(): DragSession | null {
    return this.session;
  }

  getHoverTarget(): DropTarget | null {
    return this.hoverTarget;
  }

  getPointer(): { x: number; y: number } {
    return { x: this.pointerX, y: this.pointerY };
  }

  begin(session: DragSession): void {
    this.session = session;
    this.hoverTarget = null;
    this.notify('begin');
  }

  setPointer(x: number, y: number): void {
    this.pointerX = x;
    this.pointerY = y;
    this.notify('move');
  }

  setHoverTarget(target: DropTarget | null): void {
    if (this.hoverTarget === target) return;
    this.hoverTarget = target;
    this.notify('move');
  }

  /**
   * Apply the drop. Returns true on success, false on no-op (e.g.,
   * drop-on-self). Cancels and returns false if no hover target.
   */
  commit(): boolean {
    if (!this.session) return false;
    if (!this.hoverTarget) {
      this.cancel();
      return false;
    }
    const { view: srcView, items } = this.session;
    const { view: tgtView, insertPos } = this.hoverTarget;

    // Phase 1: single-item, same-view only.
    if (items.length !== 1 || srcView !== tgtView) {
      this.cancel();
      return false;
    }

    const tr = buildMoveTransaction(srcView.state, items, insertPos);
    if (!tr) {
      this.cancel();
      return false;
    }
    srcView.dispatch(tr.scrollIntoView());

    this.session = null;
    this.hoverTarget = null;
    this.notify('end');
    return true;
  }

  cancel(): void {
    if (!this.session) return;
    this.session = null;
    this.hoverTarget = null;
    this.notify('end');
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private notify(event: DragEvent): void {
    for (const fn of this.listeners) {
      try {
        fn(event);
      } catch (err) {
        // Don't let one subscriber's error break others.
        console.error('drag listener error', err);
      }
    }
  }
}

/** Workspace-wide singleton. */
export const dragController = new DragControllerImpl();

/**
 * Build a single transaction that cuts the source range(s) and
 * re-inserts them at `insertPos`. Returns null on a no-op (drop on
 * self, or `insertPos` falls inside one of the dragged items'
 * source ranges).
 *
 * Phase 1: single-item only. Multi-item support (Phase 2) will sort
 * items by `from` descending for cuts and re-insert in original
 * document order.
 */
export function buildMoveTransaction(
  state: EditorState,
  items: DragItem[],
  insertPos: number,
): Transaction | null {
  if (items.length !== 1) return null;
  const item = items[0]!;
  if (insertPos >= item.from && insertPos <= item.to) return null;

  const slice = state.doc.slice(item.from, item.to);
  const tr = state.tr;
  tr.delete(item.from, item.to);
  const mappedTarget = tr.mapping.map(insertPos);
  tr.insert(mappedTarget, slice.content);
  return tr;
}
