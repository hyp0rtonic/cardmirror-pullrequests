/**
 * Build the context payload for the AI explainer flow.
 *
 * Walk up from the selection's `$from` position looking for the
 * innermost container (card or analytic_unit). If we find one, the
 * payload includes its tag / analytic / cite_paragraphs alongside
 * the selected text. If the selection lives at doc level, the
 * payload is selection-only — the AI just sees the text the user
 * asked about, with no surrounding card context.
 */

import type { EditorState } from 'prosemirror-state';
import type { Node as PMNode } from 'prosemirror-model';

export interface ExplainContext {
  /** The text the user selected (may span multiple paragraphs;
   *  paragraph breaks collapse to '\n'). */
  selection: string;
  /** Verbatim text of the containing card's tag, if any. */
  tag: string | null;
  /** Verbatim text of an in-card analytic paragraph or the
   *  analytic_unit's header analytic, if any. */
  analytic: string | null;
  /** All cite paragraphs in the containing container, in document
   *  order. Concatenated and shown to the model as a single block. */
  cites: string[];
}

/** Compute the explainer payload for the editor's current selection.
 *  Returns `null` when the selection is empty — callers should
 *  refuse to fire an AI request in that case. */
export function buildExplainContext(state: EditorState): ExplainContext | null {
  const { from, to } = state.selection;
  if (from === to) return null;

  const selection = state.doc.textBetween(from, to, '\n', '\n').trim();
  if (!selection) return null;

  // Walk depth ancestors from innermost outward looking for
  // a card or analytic_unit. We use $from rather than $to —
  // an unusual selection that straddles container boundaries
  // doesn't really fit the explainer flow; we take the
  // container of the start point and trust the AI to handle the
  // rest from the included selection text.
  const $pos = state.doc.resolve(from);
  let container: PMNode | null = null;
  for (let d = $pos.depth; d >= 0; d--) {
    const node = $pos.node(d);
    if (node.type.name === 'card' || node.type.name === 'analytic_unit') {
      container = node;
      break;
    }
  }

  if (!container) {
    return { selection, tag: null, analytic: null, cites: [] };
  }

  let tag: string | null = null;
  let analytic: string | null = null;
  const cites: string[] = [];
  container.forEach((child) => {
    if (child.type.name === 'tag' && tag === null) {
      tag = child.textContent.trim() || null;
    } else if (child.type.name === 'analytic' && analytic === null) {
      analytic = child.textContent.trim() || null;
    } else if (child.type.name === 'cite_paragraph') {
      const t = child.textContent.trim();
      if (t) cites.push(t);
    }
  });
  return { selection, tag, analytic, cites };
}

/** Format the context into a single user-message string. The shape
 *  is plain text rather than JSON so the model sees a natural
 *  narrative; the AI's reply will be plain prose that can land
 *  directly into a comment body. */
export function formatExplainPrompt(
  question: string,
  ctx: ExplainContext,
): string {
  const parts: string[] = [];
  parts.push(`Question: ${question.trim()}`);
  parts.push('');
  parts.push('Selected text:');
  parts.push('"""');
  parts.push(ctx.selection);
  parts.push('"""');
  if (ctx.tag || ctx.analytic || ctx.cites.length > 0) {
    parts.push('');
    parts.push('Surrounding context (from the card this selection is part of):');
    if (ctx.tag) parts.push(`Tag: ${ctx.tag}`);
    if (ctx.analytic) parts.push(`Analytic: ${ctx.analytic}`);
    for (const cite of ctx.cites) parts.push(`Cite: ${cite}`);
  }
  return parts.join('\n');
}

/** Default system prompt for the AI explainer.
 *
 * Pedagogical stance: this tool is meant to help the user *deepen
 * their own research*, not to be a final-answer oracle. Replies do
 * give a direct answer — but treat that answer as a starting point,
 * with a scaffolded search strategy so the user can read further
 * and verify / extend on their own.
 */
export const EXPLAIN_SYSTEM_PROMPT =
  "You are a research coach embedded in a competitive-debate document editor. " +
  "The user has selected a passage from a debate card and asked a question about it. " +
  "Your job is to give them a useful starting answer AND set them up to dig deeper " +
  "on their own. Use the surrounding context (tag, analytic, cite) to ground your reply.\n\n" +
  "Structure every reply in three short parts:\n" +
  "1) Direct answer: a concise, substantive response to the question — enough that " +
  "the user has a real foothold, not a brush-off. Treat this as a jumping-off point, " +
  "not the last word.\n" +
  "2) Search terms: a short list of specific phrases / keywords / author names / " +
  "Boolean queries that are likely to surface deeper or more authoritative sources.\n" +
  "3) Where to look: name specific places — academic databases (Google Scholar, " +
  "JSTOR, SSRN, the user's library), domain-specific sites (think-tank archives, " +
  "primary government sources, journalist-of-record beats, debate-camp evidence " +
  "repositories), or particular authors / journals that own the literature. " +
  "Prefer concrete venues over generic 'search the web'.\n\n" +
  "Keep the whole reply tight enough to read in a side-panel comment.";

/** Matches an `@AI` mention anywhere in a reply, case-insensitive,
 *  bounded by non-word chars or string ends. Used by the comments
 *  UI to decide whether a reply submission also fires an AI request. */
const AI_MENTION_RE = /(^|[^A-Za-z0-9])@AI(?![A-Za-z0-9])/i;

export function hasAiMention(text: string): boolean {
  return AI_MENTION_RE.test(text);
}
