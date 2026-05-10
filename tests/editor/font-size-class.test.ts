import { describe, expect, it } from 'vitest';
import { schema } from '../../src/schema/index.js';
import { computeMinHalfPoints } from '../../src/editor/font-size-class-plugin.js';

const HP_4PT = 8;
const HP_8PT = 16;
const HP_11PT = 22;
const HP_13PT = 26;

function fontSize(hp: number) {
  return schema.marks['font_size']!.create({ halfPoints: hp });
}

function bodyPara(...children: ReturnType<typeof schema.text>[]) {
  return schema.nodes['card_body']!.create(null, children);
}

describe('font-size-class plugin (computeMinHalfPoints)', () => {
  it('uniform 4pt paragraph → min is 8 (4pt half-points)', () => {
    const p = bodyPara(schema.text('all small', [fontSize(HP_4PT)]));
    expect(computeMinHalfPoints(p)).toBe(HP_4PT);
  });

  it('paragraph with no font_size marks → caps at default 22 (11pt)', () => {
    const p = bodyPara(schema.text('default sized'));
    expect(computeMinHalfPoints(p)).toBe(HP_11PT);
  });

  it('mixed 4pt + 11pt (untagged) paragraph → min is 8', () => {
    const p = bodyPara(
      schema.text('small ', [fontSize(HP_4PT)]),
      schema.text('then default'),
    );
    expect(computeMinHalfPoints(p)).toBe(HP_4PT);
  });

  it('mixed 4pt + 11pt (explicitly tagged) paragraph → min is 8', () => {
    const p = bodyPara(
      schema.text('small ', [fontSize(HP_4PT)]),
      schema.text('larger', [fontSize(HP_11PT)]),
    );
    expect(computeMinHalfPoints(p)).toBe(HP_4PT);
  });

  it('uniformly larger-than-default (13pt) → caps at default 22', () => {
    // The function caps at DEFAULT_HALF_POINTS — only sizes smaller
    // than default cause a decoration to be emitted. Larger uniform
    // text gets no class, so reporting 22 here is the correct contract.
    const p = bodyPara(schema.text('big', [fontSize(HP_13PT)]));
    expect(computeMinHalfPoints(p)).toBe(HP_11PT);
  });

  it('empty paragraph → default 22', () => {
    const p = schema.nodes['card_body']!.create(null, []);
    expect(computeMinHalfPoints(p)).toBe(HP_11PT);
  });

  it('paragraph with multiple small sizes picks the smallest', () => {
    const p = bodyPara(
      schema.text('eight ', [fontSize(HP_8PT)]),
      schema.text('four ', [fontSize(HP_4PT)]),
      schema.text('eight again', [fontSize(HP_8PT)]),
    );
    expect(computeMinHalfPoints(p)).toBe(HP_4PT);
  });
});
