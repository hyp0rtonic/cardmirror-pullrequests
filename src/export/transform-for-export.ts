/**
 * Pre-export transforms that strip / filter the doc based on the
 * Save As dialog's checkboxes. Runs BEFORE `toDocx` so the docx
 * output reflects the user's inclusion choices without the exporter
 * itself needing per-feature flags.
 *
 * Four user options drive this:
 *   - includeComments   (no-op until comments import lands)
 *   - includeAnalytics  (strip analytic_units + in-card analytic)
 *   - includeUndertags  (strip undertag nodes wherever they live)
 *   - readMode          (mutually exclusive — replaces the above
 *                        and saves only what's visible in read mode)
 *
 * Read-mode export mirrors the read-mode plugin's keep/hide rules:
 *   - Headings (pocket / hat / block / tag / analytic): kept whole.
 *   - cite_paragraph: kept, inlines filtered to those carrying
 *     cite_mark.
 *   - card_body / paragraph / undertag: kept, inlines filtered to
 *     those carrying the `highlight` mark.
 *   - Cards / analytic_units: recursed; container kept iff at least
 *     one survivor child exists.
 *   - Tables: dropped (read mode plugin doesn't model them).
 */

import type { Node as PMNode, Schema } from 'prosemirror-model';

export interface ExportTransformOptions {
  includeComments: boolean;
  includeAnalytics: boolean;
  includeUndertags: boolean;
  readMode: boolean;
}

export function transformForExport(
  doc: PMNode,
  opts: ExportTransformOptions,
): PMNode {
  if (opts.readMode) return applyReadModeTransform(doc);

  let out = doc;
  if (!opts.includeAnalytics) out = stripAnalytics(out);
  if (!opts.includeUndertags) out = stripUndertags(out);
  // includeComments is a no-op until comments import lands. The
  // exporter has no comment-emit logic yet; once it does, this is
  // where the gate plugs in.
  return out;
}

// --------------------------- read mode ---------------------------

function applyReadModeTransform(doc: PMNode): PMNode {
  const schema = doc.type.schema;
  const out: PMNode[] = [];
  doc.forEach((child) => {
    const t = transformForReadMode(child, schema);
    if (t) out.push(t);
  });
  return schema.nodes['doc']!.create(null, out);
}

function transformForReadMode(node: PMNode, schema: Schema): PMNode | null {
  const name = node.type.name;
  // Heading-shaped paragraphs survive in their entirety — they're
  // the structural skeleton the reader navigates by.
  if (name === 'pocket' || name === 'hat' || name === 'block') return node;

  // Card / analytic_unit: keep the required first heading (tag or
  // analytic), recurse into the rest.
  if (name === 'card' || name === 'analytic_unit') {
    const children: PMNode[] = [];
    node.forEach((child) => {
      const t = transformForReadMode(child, schema);
      if (t) children.push(t);
    });
    // Schema requires the first child (tag for card, analytic for
    // analytic_unit) — `transformForReadMode` keeps both as-is so the
    // container is always valid as long as we got at least one
    // survivor.
    if (children.length === 0) return null;
    return node.type.create(node.attrs, children);
  }

  // Tag / analytic standalone (inside a card / analytic_unit recursion):
  // kept whole.
  if (name === 'tag' || name === 'analytic') return node;

  // Cite paragraph: keep only text carrying cite_mark.
  if (name === 'cite_paragraph') {
    return filterParagraphByMark(node, 'cite_mark');
  }

  // Body paragraphs (card_body / generic paragraph / undertag): keep
  // only text carrying the highlight mark.
  if (name === 'card_body' || name === 'paragraph' || name === 'undertag') {
    return filterParagraphByMark(node, 'highlight');
  }

  // Tables, images, anything else: dropped.
  return null;
}

function filterParagraphByMark(node: PMNode, markName: string): PMNode | null {
  const kept: PMNode[] = [];
  node.forEach((child) => {
    if (child.isText && child.marks.some((m) => m.type.name === markName)) {
      kept.push(child);
    }
  });
  if (kept.length === 0) return null;
  return node.type.create(node.attrs, kept);
}

// --------------------------- analytics ---------------------------

function stripAnalytics(doc: PMNode): PMNode {
  const schema = doc.type.schema;
  const out: PMNode[] = [];
  doc.forEach((child) => {
    if (child.type.name === 'analytic_unit') return; // drop wholesale
    if (child.type.name === 'card') {
      out.push(filterChildren(child, (c) => c.type.name !== 'analytic'));
      return;
    }
    out.push(child);
  });
  return schema.nodes['doc']!.create(null, out);
}

// --------------------------- undertags ---------------------------

function stripUndertags(doc: PMNode): PMNode {
  const schema = doc.type.schema;
  const out: PMNode[] = [];
  doc.forEach((child) => {
    if (child.type.name === 'undertag') return; // doc-level undertag
    if (child.type.name === 'card' || child.type.name === 'analytic_unit') {
      out.push(filterChildren(child, (c) => c.type.name !== 'undertag'));
      return;
    }
    out.push(child);
  });
  return schema.nodes['doc']!.create(null, out);
}

// --------------------------- helpers -----------------------------

/** Build a copy of a container node with only the children for which
 *  `predicate` returns true. The container's required first child is
 *  preserved as long as `predicate` accepts it (the caller's
 *  responsibility — both filter-helpers above only drop
 *  optional-slot children). */
function filterChildren(node: PMNode, predicate: (child: PMNode) => boolean): PMNode {
  const kept: PMNode[] = [];
  node.forEach((child) => {
    if (predicate(child)) kept.push(child);
  });
  return node.type.create(node.attrs, kept);
}
