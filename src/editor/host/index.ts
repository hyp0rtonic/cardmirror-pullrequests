/**
 * Host singleton + platform detection.
 *
 * Picks the right Host implementation once at module load and
 * returns the same instance from every `getHost()` call. The
 * detection seam is intentionally narrow — `window.electronAPI`
 * (and later `window.__TAURI__`) is the only thing the editor
 * looks at — so the desktop wrappers know exactly what to expose
 * for their Host implementation to be selected.
 */

import { BrowserHost } from './browser-host.js';
import type { Host } from './types.js';

export type { Host, OpenedFile, SaveResult } from './types.js';

declare global {
  interface Window {
    /** Present only when the renderer is running inside an Electron
     *  shell that exposed the bridge from its preload script.
     *  Existence-only check; the actual shape is owned by the
     *  desktop app's preload code and the ElectronHost it pairs with. */
    electronAPI?: unknown;
    /** Present only inside a Tauri-bundled webview. Same role as
     *  `electronAPI` for the Tauri host (whenever that lands). */
    __TAURI__?: unknown;
  }
}

let cached: Host | null = null;

export function getHost(): Host {
  if (cached) return cached;
  // Order matters when more than one is present (shouldn't happen
  // in practice, but be explicit): native wrappers win over plain
  // browser since they expose richer capabilities.
  if (typeof window !== 'undefined' && window.electronAPI !== undefined) {
    // ElectronHost will be loaded here once the desktop shell lands;
    // until then we fall through to BrowserHost even when running
    // under Electron. That's intentional — running today's bundle
    // inside a hello-world Electron shell still works, just without
    // the native dialogs / autosave goodies.
  }
  if (typeof window !== 'undefined' && window.__TAURI__ !== undefined) {
    // Same story for the eventual Tauri host.
  }
  cached = new BrowserHost();
  return cached;
}
