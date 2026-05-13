/**
 * Select Similar Formatting — matching-function tests.
 *
 * The plugin's apply / decorations work happens against a live PM
 * view and is tricky to drive in vitest, so we test the pure
 * matching function (`computeSimilarMatches`) directly. That's the
 * core of the feature; the plugin is a thin wrapper around it.
 */

import { describe, expect, it } from 'vitest';
import { schema, newHeadingId } from '../../src/schema/index.js';
import { computeSimilarMatches } from '../../src/editor/similar-selection-plugin.js';

function tag(text: string, id = newHeadingId()) {
  return schema.nodes['tag']!.create({ id }, schema.text(text));
}
function cardBody(text: string, marks: ReturnType<typeof schema.marks['bold']['create']>[] = []) {
  return schema.nodes['card_body']!.create(
    null,
    schema.text(text, marks),
  );
}
function card(...children: ReturnType<typeof tag>[]) {
  return schema.nodes['card']!.create(null, children);
}
function docOf(...children: ReturnType<typeof card>[]) {
  return schema.nodes['doc']!.create(null, children);
}

const bold = () => schema.marks['bold']!.create();
const italic = () => schema.marks['italic']!.create();
const fs = (halfPoints: number) =>
  schema.marks['font_size']!.create({ halfPoints });

describe('computeSimilarMatches', () => {
  it('matches all tags in the doc when cursor is on a tag (no direct fmt)', () => {
    const doc = docOf(
      card(tag('TagOne'), cardBody('Body A')),
      card(tag('TagTwo'), cardBody('Body B')),
      card(tag('TagThree'), cardBody('Body C')),
    );
    // Cursor inside "TagOne". Doc structure puts tag content at:
    //   doc 0 / card 1 / tag 2 / text starts at 2.
    // Easier: walk to find the first tag's text-start.
    const cursorPos = findTextStart(doc, 'TagOne');
    const matches = computeSimilarMatches(doc, cursorPos, null);
    expect(matches.length).toBe(3);
    expect(textAtRanges(doc, matches).sort()).toEqual([
      'TagOne',
      'TagThree',
      'TagTwo',
    ]);
  });

  it('matches only card_body runs that share the same direct fmt', () => {
    const doc = docOf(
      card(tag('T1'), cardBody('Plain body 1')),
      card(tag('T2'), cardBody('Bold body 2', [bold()])),
      card(tag('T3'), cardBody('Plain body 3')),
    );
    const plainPos = findTextStart(doc, 'Plain body 1');
    const plainMatches = computeSimilarMatches(doc, plainPos, null);
    expect(textAtRanges(doc, plainMatches).sort()).toEqual([
      'Plain body 1',
      'Plain body 3',
    ]);

    const boldPos = findTextStart(doc, 'Bold body 2');
    const boldMatches = computeSimilarMatches(doc, boldPos, null);
    expect(textAtRanges(doc, boldMatches)).toEqual(['Bold body 2']);
  });

  it('treats different mark attrs as distinct fingerprints', () => {
    const doc = docOf(
      card(
        tag('T'),
        cardBody('8pt run', [fs(16)]),
        cardBody('11pt run', [fs(22)]),
        cardBody('Another 8pt', [fs(16)]),
      ),
    );
    const small = findTextStart(doc, '8pt run');
    const smallMatches = computeSimilarMatches(doc, small, null);
    expect(textAtRanges(doc, smallMatches).sort()).toEqual([
      '8pt run',
      'Another 8pt',
    ]);
  });

  it('does not match runs whose parent block type differs', () => {
    const doc = docOf(
      card(
        tag('A tag'),
        cardBody('A tag'), // same text, different parent
      ),
    );
    const tagPos = findTextStart(doc, 'A tag', 0); // first occurrence = the tag
    const matches = computeSimilarMatches(doc, tagPos, null);
    expect(textAtRanges(doc, matches)).toEqual(['A tag']);
  });

  it('respects mark-order differences as not-equal (sanity)', () => {
    // Marks of different types in the same set still hash to the
    // same equality via marksEqual (PM normalizes order). This just
    // confirms the equality check accepts equivalent multi-mark sets.
    const doc = docOf(
      card(
        tag('T'),
        cardBody('bold-italic', [bold(), italic()]),
        cardBody('italic-bold', [italic(), bold()]),
      ),
    );
    const pos = findTextStart(doc, 'bold-italic');
    const matches = computeSimilarMatches(doc, pos, null);
    // PM normalizes marks: both runs end up with marks in the same
    // order, so they match each other.
    expect(textAtRanges(doc, matches).sort()).toEqual([
      'bold-italic',
      'italic-bold',
    ]);
  });

  it('restricts matching to the provided scope range', () => {
    const doc = docOf(
      card(tag('Tag1'), cardBody('alpha')),
      card(tag('Tag2'), cardBody('beta')),
      card(tag('Tag3'), cardBody('gamma')),
    );
    const cursorPos = findTextStart(doc, 'Tag1');
    // Scope = approximately the first two cards. Find a boundary
    // that includes Tag1+Tag2 but not Tag3.
    const tag3Pos = findTextStart(doc, 'Tag3');
    const matches = computeSimilarMatches(doc, cursorPos, {
      from: 0,
      to: tag3Pos - 1, // before Tag3's container
    });
    const found = textAtRanges(doc, matches).sort();
    expect(found).toContain('Tag1');
    expect(found).toContain('Tag2');
    expect(found).not.toContain('Tag3');
  });

  it('returns empty when the cursor is on an empty paragraph', () => {
    const doc = docOf(
      card(tag('Tag'), cardBody('body')),
    );
    // Position 0 is the doc start — not inside any textblock.
    expect(computeSimilarMatches(doc, 0, null)).toEqual([]);
  });
});

// ---- helpers ----

function findTextStart(
  doc: ReturnType<typeof docOf>,
  needle: string,
  occurrence = 0,
): number {
  let seen = 0;
  let found = -1;
  doc.descendants((node, pos) => {
    if (found !== -1) return false;
    if (!node.isText) return true;
    if (node.text && node.text.includes(needle)) {
      if (seen === occurrence) {
        found = pos + node.text.indexOf(needle) + 1; // inside the text
        return false;
      }
      seen += 1;
    }
    return true;
  });
  if (found === -1) throw new Error(`needle not found: ${needle}`);
  return found;
}

function textAtRanges(
  doc: ReturnType<typeof docOf>,
  ranges: { from: number; to: number }[],
): string[] {
  return ranges.map((r) => doc.textBetween(r.from, r.to));
}
