/**
 * Dropzone bubble — a cross-window scratch shelf for dragged
 * content. UI element pinned to the bottom of the nav pane.
 *
 * Lifecycle:
 *   - Resting state: small grey bubble showing an item count.
 *   - Drag-over (something being dragged onto the bubble): expands
 *     to a wider drop target with the blue `--pmd-c-drop` accent
 *     used elsewhere for drag highlights.
 *   - Click: opens a popover above the bubble listing every item
 *     across every window. Each row has a delete button and is
 *     draggable — drag a row out and it lands at the cursor's
 *     drop target (same machinery PM uses for normal drags).
 *
 * Drag-in:
 *   Registers a DragSurface with `dragController`. Its hitTest
 *   returns the bubble's bounding rect; on commit the controller
 *   calls the surface's `absorb` callback, which extracts each
 *   item's slice from the source view (or uses the prebuilt slice
 *   for virtual sessions) and pushes it into the dropzone store.
 *
 * Drag-out:
 *   Each popover row listens for pointerdown + threshold-crossing
 *   pointermove, at which point it starts a `virtual` drag session
 *   via `dragController.begin(...)`. From there everything is
 *   standard — the controller routes the drop through the same
 *   surfaces as a normal drag.
 *
 * Store: `dropzoneStore` (electron-aware) holds the cross-window
 *   state. The bubble subscribes and re-renders on every change.
 */

import { Slice } from 'prosemirror-model';
import type { EditorView } from 'prosemirror-view';
import { dragController, type DragItem, type DragSurface } from './drag-controller.js';
import { dropzoneStore, type DropzoneItem } from './dropzone-store.js';
import { schema } from '../schema/index.js';

interface DropzoneMountOptions {
  /** The nav-pane root the bubble is anchored to. The bubble
   *  positions itself relative to this element. */
  parent: HTMLElement;
  /** Returns the currently-focused PM view (used as the source
   *  view for virtual drag sessions). Some downstream code in the
   *  controller derefs the session view — even though it doesn't
   *  read its doc for virtual sessions, the session shape still
   *  requires one. */
  getFocusedView: () => EditorView | null;
}

export class DropzoneController {
  private root!: HTMLDivElement;
  private bubble!: HTMLButtonElement;
  private countBadge!: HTMLSpanElement;
  private popover: HTMLDivElement | null = null;
  private items: DropzoneItem[] = [];
  private surface: DragSurface | null = null;
  private unregisterSurface: (() => void) | null = null;
  private unsubscribeStore: (() => void) | null = null;
  private unsubscribeController: (() => void) | null = null;
  private getFocusedView: () => EditorView | null = () => null;
  // Drag-out pointer-tracking state.
  private dragOutSource: {
    startX: number;
    startY: number;
    item: DropzoneItem;
    started: boolean;
  } | null = null;

  mount(opts: DropzoneMountOptions): void {
    this.getFocusedView = opts.getFocusedView;

    this.root = document.createElement('div');
    this.root.className = 'pmd-dropzone-root';

    this.bubble = document.createElement('button');
    this.bubble.type = 'button';
    this.bubble.className = 'pmd-dropzone-bubble';
    this.bubble.setAttribute('aria-label', 'Dropzone shelf');
    this.bubble.title = 'Dropzone — drag content here, then drop elsewhere to reuse';

    const icon = document.createElement('span');
    icon.className = 'pmd-dropzone-icon';
    icon.setAttribute('aria-hidden', 'true');
    // Inline SVG (avoids a font-glyph dependency on the user-chosen
    // UI font). A simple tray-with-arrow glyph.
    icon.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/><path d="M12 14V4"/><path d="M8 8l4-4 4 4"/></svg>';
    this.bubble.appendChild(icon);

    this.countBadge = document.createElement('span');
    this.countBadge.className = 'pmd-dropzone-count';
    this.countBadge.hidden = true;
    this.bubble.appendChild(this.countBadge);

    this.bubble.addEventListener('click', (e) => {
      e.stopPropagation();
      this.togglePopover();
    });

    this.root.appendChild(this.bubble);
    opts.parent.appendChild(this.root);

    // Drag surface — bubble accepts drops, popover content area
    // also accepts drops (drop-on-popover same as drop-on-bubble).
    this.surface = {
      hitTest: (clientX, clientY) => {
        const rect = this.bubble.getBoundingClientRect();
        const popRect = this.popover?.getBoundingClientRect();
        const inBubble =
          clientX >= rect.left &&
          clientX <= rect.right &&
          clientY >= rect.top &&
          clientY <= rect.bottom;
        const inPop =
          popRect != null &&
          clientX >= popRect.left &&
          clientX <= popRect.right &&
          clientY >= popRect.top &&
          clientY <= popRect.bottom;
        if (!inBubble && !inPop) return null;
        return {
          el: this.bubble,
          insertPos: 0,
          dy: 0,
          absorb: (items) => this.absorbItems(items),
        };
      },
      highlight: (el) => {
        this.bubble.classList.toggle('pmd-dropzone-bubble-drop-target', el !== null);
      },
    };
    this.unregisterSurface = dragController.registerSurface(this.surface);

    // Store subscription — re-render on every change.
    void dropzoneStore.init().then(() => {
      this.items = dropzoneStore.list();
      this.render();
    });
    this.unsubscribeStore = dropzoneStore.subscribe((items) => {
      this.items = items;
      this.render();
    });

    // Controller subscription — clean up drag-out state when a
    // session ends (regardless of how it ended).
    this.unsubscribeController = dragController.subscribe((event) => {
      if (event === 'end') {
        this.endDragOut();
      }
    });

    // Click-outside closes the popover.
    document.addEventListener('pointerdown', this.onDocumentPointerDown);
  }

  unmount(): void {
    document.removeEventListener('pointerdown', this.onDocumentPointerDown);
    this.unsubscribeStore?.();
    this.unsubscribeController?.();
    this.unregisterSurface?.();
    this.closePopover();
    this.root.remove();
  }

  // ---- Rendering ----------------------------------------------------

  private render(): void {
    const n = this.items.length;
    this.countBadge.hidden = n === 0;
    this.countBadge.textContent = String(n);
    this.bubble.classList.toggle('pmd-dropzone-bubble-empty', n === 0);
    if (this.popover) this.renderPopover();
  }

  private togglePopover(): void {
    if (this.popover) this.closePopover();
    else this.openPopover();
  }

  private openPopover(): void {
    this.popover = document.createElement('div');
    this.popover.className = 'pmd-dropzone-popover';
    // Anchor above the bubble. The popover is `position: fixed`
    // so it's not clipped by the nav-pane's overflow.
    document.body.appendChild(this.popover);
    this.renderPopover();
    this.bubble.classList.add('pmd-dropzone-bubble-open');
    this.repositionPopover();
    window.addEventListener('resize', this.repositionPopover);
  }

  private closePopover(): void {
    if (!this.popover) return;
    this.popover.remove();
    this.popover = null;
    this.bubble.classList.remove('pmd-dropzone-bubble-open');
    window.removeEventListener('resize', this.repositionPopover);
  }

  private renderPopover(): void {
    if (!this.popover) return;
    this.popover.innerHTML = '';

    const header = document.createElement('div');
    header.className = 'pmd-dropzone-popover-header';
    const title = document.createElement('span');
    title.className = 'pmd-dropzone-popover-title';
    title.textContent = this.items.length === 0
      ? 'Dropzone shelf'
      : `Dropzone shelf — ${this.items.length} item${this.items.length === 1 ? '' : 's'}`;
    header.appendChild(title);
    if (this.items.length > 0) {
      const clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'pmd-dropzone-popover-clear';
      clear.textContent = 'Clear all';
      clear.title = 'Remove every shelf item';
      clear.addEventListener('click', () => {
        void dropzoneStore.clear();
      });
      header.appendChild(clear);
    }
    this.popover.appendChild(header);

    if (this.items.length === 0) {
      const empty = document.createElement('p');
      empty.className = 'pmd-dropzone-popover-empty';
      empty.textContent =
        'Drag a card, heading, or selection onto the bubble below. Items here are shared across windows in this session.';
      this.popover.appendChild(empty);
      this.repositionPopover();
      return;
    }

    const list = document.createElement('ul');
    list.className = 'pmd-dropzone-list';
    // Newest first.
    for (const item of [...this.items].reverse()) {
      list.appendChild(this.renderRow(item));
    }
    this.popover.appendChild(list);
    this.repositionPopover();
  }

  private renderRow(item: DropzoneItem): HTMLLIElement {
    const row = document.createElement('li');
    row.className = 'pmd-dropzone-row';

    const handle = document.createElement('span');
    handle.className = 'pmd-dropzone-row-handle';
    handle.setAttribute('aria-hidden', 'true');
    handle.textContent = '⋮⋮';
    row.appendChild(handle);

    const label = document.createElement('span');
    label.className = 'pmd-dropzone-row-label';
    label.textContent = item.label;
    label.title = item.label;
    row.appendChild(label);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'pmd-dropzone-row-delete';
    del.title = 'Remove from shelf';
    del.setAttribute('aria-label', 'Remove');
    del.textContent = '×';
    del.addEventListener('click', (e) => {
      e.stopPropagation();
      void dropzoneStore.remove(item.id);
    });
    row.appendChild(del);

    // Drag-out: pointerdown starts tracking, pointermove past the
    // threshold begins a virtual drag session via the controller.
    row.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      // Ignore clicks on the delete button.
      if ((e.target as HTMLElement).closest('.pmd-dropzone-row-delete')) return;
      this.dragOutSource = {
        startX: e.clientX,
        startY: e.clientY,
        item,
        started: false,
      };
      window.addEventListener('pointermove', this.onDragOutPointerMove);
      window.addEventListener('pointerup', this.onDragOutPointerUp);
      // Prevent text-selection from the row's label intercepting
      // the drag gesture.
      e.preventDefault();
    });

    return row;
  }

  // ---- Drag-in (controller absorb) ----------------------------------

  private async absorbItems(items: DragItem[]): Promise<void> {
    const session = dragController.getSession();
    if (!session) return;
    const srcView = session.view;
    for (const item of items) {
      const slice = item.prebuilt ?? srcView.state.doc.slice(item.from, item.to);
      const sliceJson = slice.toJSON();
      const label = deriveLabel(slice, item);
      const id = newId();
      await dropzoneStore.add({
        id,
        label,
        sliceJson,
        createdAt: Date.now(),
      });
    }
  }

  // ---- Drag-out (start a virtual session) ---------------------------

  private onDragOutPointerMove = (e: PointerEvent): void => {
    const src = this.dragOutSource;
    if (!src) return;
    if (!src.started) {
      const dx = e.clientX - src.startX;
      const dy = e.clientY - src.startY;
      if (dx * dx + dy * dy < 16) return; // < 4 px threshold
      src.started = this.beginDragOut(src.item);
      if (!src.started) {
        // No focused view → can't start a virtual session; bail.
        this.endDragOut();
        return;
      }
    }
    dragController.setPointer(e.clientX, e.clientY);
    dragController.dispatchHit(e.clientX, e.clientY);
  };

  private onDragOutPointerUp = (_e: PointerEvent): void => {
    if (!this.dragOutSource) return;
    if (this.dragOutSource.started) {
      dragController.commit({ copy: true });
    }
    this.endDragOut();
  };

  private beginDragOut(item: DropzoneItem): boolean {
    const view = this.getFocusedView();
    if (!view) return false;
    let slice: Slice;
    try {
      slice = Slice.fromJSON(schema, item.sliceJson as Parameters<typeof Slice.fromJSON>[1]);
    } catch {
      return false;
    }
    const dragItem: DragItem = {
      from: 0,
      to: 0,
      id: null,
      type: 'dropzone',
      level: 0,
      label: item.label,
      prebuilt: slice,
    };
    dragController.begin({ view, items: [dragItem], virtual: true });
    return true;
  }

  private endDragOut(): void {
    if (!this.dragOutSource) return;
    window.removeEventListener('pointermove', this.onDragOutPointerMove);
    window.removeEventListener('pointerup', this.onDragOutPointerUp);
    this.dragOutSource = null;
  }

  // ---- Misc utilities -----------------------------------------------

  private onDocumentPointerDown = (e: PointerEvent): void => {
    if (!this.popover) return;
    const t = e.target as Node | null;
    if (!t) return;
    if (this.bubble.contains(t) || this.popover.contains(t)) return;
    this.closePopover();
  };

  private repositionPopover = (): void => {
    if (!this.popover) return;
    const r = this.bubble.getBoundingClientRect();
    // Pop above and aligned with the bubble's left edge. Clamped to
    // viewport so it doesn't slip off the right or top edges.
    const popRect = this.popover.getBoundingClientRect();
    const margin = 8;
    let left = r.left;
    if (left + popRect.width > window.innerWidth - margin) {
      left = window.innerWidth - margin - popRect.width;
    }
    if (left < margin) left = margin;
    let top = r.top - popRect.height - 8;
    if (top < margin) top = r.bottom + 8;
    this.popover.style.left = `${left}px`;
    this.popover.style.top = `${top}px`;
  };
}

function newId(): string {
  return `dz-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function deriveLabel(slice: Slice, item: DragItem): string {
  // Prefer the source item's label when present (heading drag from
  // the nav pane → already a human label). Otherwise derive from
  // the slice's textContent.
  if (item.label && item.label.trim()) {
    const l = item.label.trim();
    return l.length > 80 ? l.slice(0, 78) + '…' : l;
  }
  const text = slice.content.textBetween(0, slice.content.size, ' ', ' ').trim();
  if (text) return text.length > 80 ? text.slice(0, 78) + '…' : text;
  // Empty slice (e.g., a structural-only drag) — fall back to type.
  return item.type ? `(${item.type})` : '(item)';
}

