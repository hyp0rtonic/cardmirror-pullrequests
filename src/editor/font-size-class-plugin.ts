/**
 * Font-size class plugin.
 *
 * Tags each body paragraph with `pmd-fs-shrunk` plus an inline
 * `style="font-size: Xpt; line-height: Y"` reflecting the *smallest*
 * font-size among its text nodes. The inline style lowers the
 * paragraph element's own font-size, which shrinks the paragraph's
 * strut so uniformly-small paragraphs can pack tightly.
 *
 * Why this is needed: `font_size` is a mark, so it renders as inline
 * `<span style="font-size: ...">`. The wrapping `<p>` element keeps
 * the inherited body size, and CSS line-boxes always include a hidden
 * "strut" at the block element's own font-size × line-height. Without
 * this plugin, a paragraph whose every span is 4pt still has a
 * ~15.4pt-tall strut (11pt × 1.4), and lines never collapse below
 * that.
 *
 * Why named-style cascade is contained: scoped CSS rules
 * (`.pmd-fs-shrunk .pmd-underline`, etc.) pin the named-style mark
 * wrappers' font-size *only when inside a shrunk paragraph*. In
 * non-shrunk contexts (headings, normal body), they inherit naturally
 * — so underlined text in a Tag still renders at the Tag's 13pt. Only
 * truly bare text (no marks at all, rare in body paragraphs) cascades
 * to the small size.
 *
 * Min, not max: in mixed-size lines (small connective + named-style
 * evidence), CSS's line-box-takes-the-tallest rule means the larger
 * spans dictate line height. Using the min therefore only changes the
 * strut, which is what matters in the uniform-small case and is a
 * no-op in the mixed-size case.
 *
 * Why inline style instead of size-specific classes: arbitrary
 * font_size mark values (any half-points integer) need to map to a
 * font-size — pre-enumerated CSS rules would have gaps for unusual
 * values (e.g. 3pt, 2pt, 5.5pt). Inline style handles any value.
 */

import { Plugin } from 'prosemirror-state';
import { Decoration, DecorationSet } from 'prosemirror-view';
import type { Node as PMNode } from 'prosemirror-model';

const BODY_PARA_TYPES = new Set([
  'card_body',
  'paragraph',
  'cite_paragraph',
  'undertag',
]);

/** OOXML default body size: 11pt = 22 half-points. */
const DEFAULT_HALF_POINTS = 22;

export const fontSizeClassPlugin: Plugin<DecorationSet> = new Plugin<DecorationSet>({
  state: {
    init(_, { doc }) {
      return computeDecorations(doc);
    },
    apply(tr, prev) {
      if (!tr.docChanged) return prev;
      return computeDecorations(tr.doc);
    },
  },
  props: {
    decorations(state) {
      return fontSizeClassPlugin.getState(state);
    },
  },
});

function computeDecorations(doc: PMNode): DecorationSet {
  const decos: Decoration[] = [];
  doc.descendants((node, pos) => {
    if (!BODY_PARA_TYPES.has(node.type.name)) return;

    const minHp = computeMinHalfPoints(node);
    if (minHp >= DEFAULT_HALF_POINTS) return;

    const fontSizePt = minHp / 2;
    const lineHeight = lineHeightFor(minHp);
    decos.push(
      Decoration.node(pos, pos + node.nodeSize, {
        class: 'pmd-fs-shrunk',
        style: `font-size: ${fontSizePt}pt; line-height: ${lineHeight}`,
      }),
    );
  });
  return DecorationSet.create(doc, decos);
}

/**
 * Line-height multiplier scaled by the shrunk size. Smaller text packs
 * tighter; sizes near the default ease toward the regular 1.4. Mixed
 * lines (containing larger named-style content) aren't affected — the
 * larger spans' own line-height dictates the line-box.
 */
function lineHeightFor(hp: number): number {
  if (hp <= 12) return 1;     // ≤ 6pt
  if (hp <= 14) return 1.1;   // 7pt
  if (hp <= 16) return 1.2;   // 8pt
  if (hp <= 18) return 1.3;   // 9pt
  if (hp <= 20) return 1.35;  // 10pt
  return 1.4;                 // ≥ 11pt (shouldn't hit; default isn't decorated)
}

/**
 * Smallest `font_size` half-points value across all text nodes in
 * `para`, capped at the default 22 (11pt). Text without a `font_size`
 * mark counts as the default.
 */
export function computeMinHalfPoints(para: PMNode): number {
  let min = DEFAULT_HALF_POINTS;
  para.descendants((child) => {
    if (!child.isText || !child.text) return;
    const fontSizeMark = child.marks.find((m) => m.type.name === 'font_size');
    const hp = fontSizeMark
      ? Number(fontSizeMark.attrs['halfPoints'] ?? DEFAULT_HALF_POINTS)
      : DEFAULT_HALF_POINTS;
    if (hp < min) min = hp;
  });
  return min;
}
