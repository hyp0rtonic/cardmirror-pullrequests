/**
 * ZIP/XML-level pruning of unused styles from .docx files — a faithful port of
 * the scouting-assistant `style_pruner.py`. Runs entirely client-side over the
 * `Docx` (JSZip) layer; no python-docx, no server.
 *
 *   - prune_unused_styles: drop style definitions nothing references
 *     (transitive over basedOn/link), keeping a protected + always-keep set.
 *   - fix_dangling_style_refs: strip references (pStyle/rStyle/tblStyle and
 *     basedOn/link/next) that point at a style id that no longer exists — the
 *     fix for Word's "found unreadable content" error after style removal.
 */

import { Docx } from '../docx.js';
import { PROTECTED_STYLE_IDS } from './template-styles.js';

const W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';
const ALWAYS_KEEP_NAMES = new Set(['Default Paragraph Font']);

/** `w:(pStyle|rStyle|tblStyle) w:val="..."` — direct style references. */
const STYLE_ATTR_RE = /w:(?:pStyle|rStyle|tblStyle)\s+w:val="([^"]+)"/g;

const CONTENT_STYLE_TAGS = ['pStyle', 'rStyle', 'tblStyle'];
const STYLE_XREF_TAGS = ['basedOn', 'link', 'next'];

function isWordXml(path: string): boolean {
  return path.startsWith('word/') && path.endsWith('.xml');
}

function attrW(el: Element, local: string): string | null {
  // OOXML attributes are emitted with the w: prefix; DOM exposes them both via
  // the namespace and (commonly) the literal qualified name.
  return el.getAttributeNS(W, local) ?? el.getAttribute(`w:${local}`);
}

function styleElements(stylesDoc: Document): Element[] {
  return Array.from(stylesDoc.getElementsByTagNameNS(W, 'style'));
}

function firstChildVal(style: Element, local: string): string | null {
  const els = style.getElementsByTagNameNS(W, local);
  return els.length ? attrW(els[0]!, 'val') : null;
}

function collectDirectRefs(xmlTexts: string[]): Set<string> {
  const refs = new Set<string>();
  for (const text of xmlTexts) {
    for (const m of text.matchAll(STYLE_ATTR_RE)) refs.add(m[1]!);
  }
  return refs;
}

function buildDepMap(stylesDoc: Document): Map<string, Set<string>> {
  const deps = new Map<string, Set<string>>();
  for (const style of styleElements(stylesDoc)) {
    const sid = attrW(style, 'styleId');
    if (sid === null) continue;
    const required = new Set<string>();
    for (const tag of ['basedOn', 'link']) {
      const val = firstChildVal(style, tag);
      if (val) required.add(val);
    }
    deps.set(sid, required);
  }
  return deps;
}

function transitiveClosure(seeds: Set<string>, deps: Map<string, Set<string>>): Set<string> {
  const needed = new Set(seeds);
  let frontier = new Set(seeds);
  while (frontier.size) {
    const next = new Set<string>();
    for (const sid of frontier) {
      for (const dep of deps.get(sid) ?? []) {
        if (!needed.has(dep)) {
          needed.add(dep);
          next.add(dep);
        }
      }
    }
    frontier = next;
  }
  return needed;
}

function alwaysKeep(style: Element): boolean {
  if (attrW(style, 'default') === '1') return true;
  const names = style.getElementsByTagNameNS(W, 'name');
  if (names.length) {
    const nameVal = attrW(names[0]!, 'val') ?? '';
    if (ALWAYS_KEEP_NAMES.has(nameVal)) return true;
  }
  return false;
}

const XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';

/** Port of `prune_unused_styles`. Returns the (possibly unchanged) bytes and
 *  the number of style definitions removed. */
export async function pruneUnusedStyles(fileBytes: Uint8Array): Promise<{ bytes: Uint8Array; removed: number }> {
  const docx = await Docx.load(fileBytes);
  const stylesXml = await docx.readText('word/styles.xml');
  if (stylesXml === null) return { bytes: fileBytes, removed: 0 };

  // Scan ALL word/*.xml (except styles.xml) for direct references.
  const xmlTexts: string[] = [];
  for (const path of docx.paths()) {
    if (isWordXml(path) && path !== 'word/styles.xml') {
      const t = await docx.readText(path);
      if (t !== null) xmlTexts.push(t);
    }
  }

  const stylesDoc = new DOMParser().parseFromString(stylesXml, 'application/xml');
  const depMap = buildDepMap(stylesDoc);

  let needed = transitiveClosure(collectDirectRefs(xmlTexts), depMap);
  for (const id of PROTECTED_STYLE_IDS) needed.add(id);
  for (const style of styleElements(stylesDoc)) {
    if (alwaysKeep(style)) {
      const sid = attrW(style, 'styleId');
      if (sid) needed.add(sid);
    }
  }
  needed = transitiveClosure(needed, depMap);

  let removed = 0;
  for (const style of styleElements(stylesDoc)) {
    const sid = attrW(style, 'styleId');
    if (sid === null || !needed.has(sid)) {
      style.parentNode?.removeChild(style);
      removed++;
    }
  }

  if (removed === 0) return { bytes: fileBytes, removed: 0 };

  const serialized = XML_DECL + new XMLSerializer().serializeToString(stylesDoc);
  docx.writeText('word/styles.xml', serialized);
  return { bytes: await docx.toBuffer(), removed };
}

/** Port of `fix_dangling_style_refs`. Always run after cleaning. */
export async function fixDanglingStyleRefs(fileBytes: Uint8Array): Promise<{ bytes: Uint8Array; removed: number }> {
  const docx = await Docx.load(fileBytes);
  const stylesXml = await docx.readText('word/styles.xml');
  if (stylesXml === null) return { bytes: fileBytes, removed: 0 };

  const definedIds = new Set<string>();
  for (const m of stylesXml.matchAll(/w:styleId="([^"]+)"/g)) definedIds.add(m[1]!);

  let totalRemoved = 0;
  const changed: string[] = [];

  const stripTags = (text: string, tags: string[]): string => {
    let out = text;
    for (const tag of tags) {
      const re = new RegExp(`<w:${tag}\\s+w:val="([^"]+)"\\s*/?>`, 'g');
      out = out.replace(re, (whole, val: string) => {
        if (!definedIds.has(val)) {
          totalRemoved++;
          return '';
        }
        return whole;
      });
    }
    return out;
  };

  // styles.xml internal cross-references (basedOn / link / next).
  const newStyles = stripTags(stylesXml, STYLE_XREF_TAGS);
  if (newStyles !== stylesXml) {
    docx.writeText('word/styles.xml', newStyles);
    changed.push('word/styles.xml');
  }

  // content files (pStyle / rStyle / tblStyle).
  for (const path of docx.paths()) {
    if (!isWordXml(path) || path === 'word/styles.xml') continue;
    const text = await docx.readText(path);
    if (text === null) continue;
    const newText = stripTags(text, CONTENT_STYLE_TAGS);
    if (newText !== text) {
      docx.writeText(path, newText);
      changed.push(path);
    }
  }

  if (changed.length === 0) return { bytes: fileBytes, removed: 0 };
  return { bytes: await docx.toBuffer(), removed: totalRemoved };
}
