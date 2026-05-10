import { describe, expect, it } from 'vitest';
import { EditorState } from 'prosemirror-state';
import { schema, newHeadingId } from '../../src/schema/index.js';
import { buildMoveTransaction, type DragItem } from '../../src/editor/drag-controller.js';

function pocket(text: string) {
  return schema.nodes['pocket']!.create({ id: newHeadingId() }, schema.text(text));
}

function block(text: string) {
  return schema.nodes['block']!.create({ id: newHeadingId() }, schema.text(text));
}

function cardWith(tagText: string, bodyText?: string) {
  const children = [
    schema.nodes['tag']!.create({ id: newHeadingId() }, schema.text(tagText)),
  ];
  if (bodyText) {
    children.push(schema.nodes['card_body']!.create(null, schema.text(bodyText)));
  }
  return schema.nodes['card']!.createChecked(null, children);
}

function makeDoc(...children: ReturnType<typeof block>[]) {
  return schema.nodes['doc']!.createChecked(null, children);
}

function dragItemForRange(from: number, to: number, type: string, level: number): DragItem {
  return { from, to, id: null, type, level, label: '' };
}

describe('buildMoveTransaction', () => {
  it('moves a card to a position before another card', () => {
    const card1 = cardWith('First');
    const card2 = cardWith('Second');
    const doc = makeDoc(card1, card2);
    const state = EditorState.create({ doc, schema });

    // Drag card2 to the position before card1.
    const card2Pos = 0 + card1.nodeSize; // start of card2
    const card2End = card2Pos + card2.nodeSize;
    const item = dragItemForRange(card2Pos, card2End, 'card', 4);
    const targetPos = 0; // before card1

    const tr = buildMoveTransaction(state, [item], targetPos);
    expect(tr).not.toBeNull();
    const newDoc = tr!.doc;
    expect(newDoc.childCount).toBe(2);
    expect(newDoc.child(0).firstChild!.textContent).toBe('Second');
    expect(newDoc.child(1).firstChild!.textContent).toBe('First');
  });

  it('moves a card to the end of the doc', () => {
    const card1 = cardWith('First');
    const card2 = cardWith('Second');
    const doc = makeDoc(card1, card2);
    const state = EditorState.create({ doc, schema });

    // Drag card1 to the very end of the doc.
    const item = dragItemForRange(0, card1.nodeSize, 'card', 4);
    const targetPos = doc.content.size;

    const tr = buildMoveTransaction(state, [item], targetPos);
    expect(tr).not.toBeNull();
    const newDoc = tr!.doc;
    expect(newDoc.child(0).firstChild!.textContent).toBe('Second');
    expect(newDoc.child(1).firstChild!.textContent).toBe('First');
  });

  it('preserves a card body when moving the card', () => {
    const card1 = cardWith('Tag1', 'body1');
    const card2 = cardWith('Tag2');
    const doc = makeDoc(card1, card2);
    const state = EditorState.create({ doc, schema });

    // Move card1 to after card2.
    const item = dragItemForRange(0, card1.nodeSize, 'card', 4);
    const targetPos = doc.content.size;
    const tr = buildMoveTransaction(state, [item], targetPos);
    expect(tr).not.toBeNull();
    const newDoc = tr!.doc;
    expect(newDoc.childCount).toBe(2);
    const movedCard = newDoc.child(1);
    expect(movedCard.firstChild!.textContent).toBe('Tag1');
    expect(movedCard.lastChild!.type.name).toBe('card_body');
    expect(movedCard.lastChild!.textContent).toBe('body1');
  });

  it('returns null when target is inside the source range (drop on self)', () => {
    const card1 = cardWith('First');
    const card2 = cardWith('Second');
    const doc = makeDoc(card1, card2);
    const state = EditorState.create({ doc, schema });

    // Drag card1; target somewhere inside it.
    const item = dragItemForRange(0, card1.nodeSize, 'card', 4);
    const insidePos = 1; // inside card1's content
    const tr = buildMoveTransaction(state, [item], insidePos);
    expect(tr).toBeNull();
  });

  it('moves a Block (heading + subordinate cards) as one unit', () => {
    // Doc: [block A][card a1 under block A][block B][card b1 under block B]
    const blockA = block('Block A');
    const cardA1 = cardWith('A1');
    const blockB = block('Block B');
    const cardB1 = cardWith('B1');
    const doc = makeDoc(blockA, cardA1, blockB, cardB1);
    const state = EditorState.create({ doc, schema });

    // Block A's range = block A heading + card A1.
    const blockARange = blockA.nodeSize + cardA1.nodeSize;
    const item = dragItemForRange(0, blockARange, 'block', 3);

    // Drop after block B's range (i.e., end of doc).
    const targetPos = doc.content.size;
    const tr = buildMoveTransaction(state, [item], targetPos);
    expect(tr).not.toBeNull();
    const newDoc = tr!.doc;
    // Order should now be: blockB, cardB1, blockA, cardA1
    expect(newDoc.child(0).type.name).toBe('block');
    expect(newDoc.child(0).textContent).toBe('Block B');
    expect(newDoc.child(1).type.name).toBe('card');
    expect(newDoc.child(2).type.name).toBe('block');
    expect(newDoc.child(2).textContent).toBe('Block A');
    expect(newDoc.child(3).type.name).toBe('card');
  });

  it('moves a Pocket and its subordinate Hat/Block/Card content together', () => {
    const pocketA = pocket('A');
    const cardA = cardWith('A-card');
    const pocketB = pocket('B');
    const cardB = cardWith('B-card');
    const doc = makeDoc(pocketA, cardA, pocketB, cardB);
    const state = EditorState.create({ doc, schema });

    const pocketARange = pocketA.nodeSize + cardA.nodeSize;
    const item = dragItemForRange(0, pocketARange, 'pocket', 1);
    const targetPos = doc.content.size;
    const tr = buildMoveTransaction(state, [item], targetPos);
    expect(tr).not.toBeNull();
    const newDoc = tr!.doc;
    // Pocket A and its card should now be at the end.
    expect(newDoc.child(0).textContent).toBe('B');
    expect(newDoc.child(2).textContent).toBe('A');
    expect(newDoc.child(3).firstChild!.textContent).toBe('A-card');
  });

  it('returns null for multi-item input (Phase 2 not yet supported)', () => {
    const card1 = cardWith('First');
    const card2 = cardWith('Second');
    const doc = makeDoc(card1, card2);
    const state = EditorState.create({ doc, schema });

    const items: DragItem[] = [
      dragItemForRange(0, card1.nodeSize, 'card', 4),
      dragItemForRange(card1.nodeSize, card1.nodeSize + card2.nodeSize, 'card', 4),
    ];
    const tr = buildMoveTransaction(state, items, doc.content.size);
    expect(tr).toBeNull();
  });
});
