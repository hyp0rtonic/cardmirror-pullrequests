/**
 * Read-only diagnostic info about the running install, shown at
 * the bottom of Settings → General. Each entry is a label / value
 * pair the user can copy-paste into a bug report.
 *
 * No host-specific plumbing — everything's derived from things the
 * renderer can see on its own: `package.json` (Vite supports JSON
 * imports natively), the `getHost()` singleton, and `navigator`.
 * Keeps this file build-time-stable without preload-bridge round-
 * trips for what's purely cosmetic metadata.
 */

import pkg from '../../package.json';
import { getHost } from './host/index.js';

export interface InstallInfoEntry {
  label: string;
  /** Human-friendly main value, e.g. "0.1.0-alpha.1". */
  value: string;
  /** Whether to display the value monospaced (URLs, UA strings,
   *  long technical IDs). Default false. */
  mono?: boolean;
}

export function getInstallInfo(): InstallInfoEntry[] {
  const hostKind = getHost().kind;
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';
  return [
    { label: 'Version', value: pkg.version },
    {
      label: 'Host',
      value: hostKind === 'electron' ? 'Desktop (Electron)' : 'Web browser',
    },
    { label: 'Operating system', value: detectOS(ua) },
    { label: 'User agent', value: ua, mono: true },
  ];
}

/** Best-effort OS detection from a user-agent string. The UA is the
 *  only cross-platform-uniform source we can read from the renderer
 *  without going through Electron's preload — `navigator.platform`
 *  is deprecated and increasingly returns generic values. */
function detectOS(ua: string): string {
  if (!ua) return 'Unknown';
  if (ua.includes('Mac OS X') || ua.includes('Macintosh')) return 'macOS';
  if (ua.includes('Windows')) return 'Windows';
  // Order matters: "Linux" appears in Android UAs too, so check
  // Android first.
  if (ua.includes('Android')) return 'Android';
  if (ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';
  if (ua.includes('Linux')) return 'Linux';
  return 'Unknown';
}
