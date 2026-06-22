/**
 * Headless .docx style cleaner for Verbatim-standard formatting — a faithful
 * TypeScript port of the scouting-assistant `style_cleaner.py`, running over the
 * python-docx-equivalent shim (`ooxml-doc.ts`). Pipeline (clean_document_bytes):
 *   pre-prune (optional) → normalize aliases → formatting→styles conversion →
 *   rename/remove style defs → save → post-prune (optional) → fix dangling refs.
 *
 * Behavior is matched to python-docx 1.1.0 as the scouting tool relies on it
 * (see ooxml-doc.ts fidelity notes). The one knowingly-reproduced quirk: in the
 * number-sequence branch of process_entirely_bold the citation set is built from
 * a fresh `paragraph.runs` call, so by object identity it matches nothing and
 * every run is cleared — identical to the Python.
 */

import { Docx } from '../docx.js';
import { OoxmlDoc, type Paragraph, type Run } from './ooxml-doc.js';
import { COMBINED_STYLE_MAP } from './template-styles.js';
import { pruneUnusedStyles, fixDanglingStyleRefs } from './style-pruner.js';

// ── normalize_style_definitions ──────────────────────────────────────

function normalizeStyleDefinitions(doc: OoxmlDoc): void {
  const targetNames: Record<string, string[]> = {
    Style13ptBold: ['Style 13 pt Bold', 'Cite', 'Old Cite'],
    StyleUnderline: ['Style Underline', 'Underline'],
    Emphasis: ['Emphasis'],
  };
  for (const style of doc.styles.all()) {
    const name = style.name;
    if (name === null) continue;
    const aliasStr = style.getAlias();
    if (!aliasStr) continue;
    const aliases = aliasStr.split(',').map((a) => a.trim());
    for (const [target, acceptable] of Object.entries(targetNames)) {
      if (acceptable.includes(name) && aliases.includes(target)) {
        style.name = target;
        const newAliases = aliases.filter((a) => a !== target);
        newAliases.push(name);
        style.setAlias(newAliases.join(','));
        break;
      }
    }
  }
}

// ── verify_style_availability / _get_style_variation ─────────────────

function verifyStyleAvailability(doc: OoxmlDoc): void {
  const groups: Record<string, string[]> = {
    citation: ['Style13ptBold', 'Style 13 pt Bold'],
    underline: ['StyleUnderline', 'Style Underline'],
    emphasis: ['Emphasis'],
  };
  const missing = Object.entries(groups)
    .filter(([, vars]) => !vars.some((v) => doc.styles.has(v)))
    .map(([purpose]) => purpose);
  if (missing.length) {
    throw new Error(
      `Document missing required style types: ${missing.join(', ')}. ` +
        'Please ensure document has appropriate styles for: ' +
        'citation, underlining, and emphasis formatting.',
    );
  }
}

const VARIATIONS: Record<string, string[]> = {
  Style13ptBold: ['Style13ptBold', 'Style 13 pt Bold'],
  StyleUnderline: ['StyleUnderline', 'Style Underline'],
  Emphasis: ['Emphasis'],
};

function getStyleVariation(doc: OoxmlDoc, base: string): string {
  const vars = VARIATIONS[base];
  if (!vars) return base;
  for (const v of vars) if (doc.styles.has(v)) return v;
  return base;
}

// ── run / paragraph analysis helpers ─────────────────────────────────

function checkEntirelyBold(paragraph: Paragraph): Run[] | null {
  const allRuns = paragraph.runs.filter((r) => r.text.trim() !== '');
  if (!allRuns.length) return null;
  return allRuns.every((r) => r.realBold()) ? allRuns : null;
}

function paragraphHasText(paragraph: Paragraph): boolean {
  return paragraph.runs.some((r) => r.text.trim() !== '');
}

/** `_find_font_size_variation` — the runs larger than the most common size. */
function findFontSizeVariation(runs: Run[]): Run[] | null {
  const sizeData: [Run, number][] = [];
  for (const run of runs) {
    const sp = run.font.sizePt;
    if (sp !== null && sp >= 6 && sp <= 72) sizeData.push([run, sp]);
  }
  if (!sizeData.length) return null;
  const counts = new Map<number, number>();
  for (const [, size] of sizeData) {
    const rounded = Math.round(size * 2) / 2;
    counts.set(rounded, (counts.get(rounded) ?? 0) + 1);
  }
  // sort by (-count, size); base = most frequent (ties → smaller size).
  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0]);
  const baseSize = sorted[0]![0];
  const larger = sizeData.filter(([, s]) => s > baseSize + 0.5).map(([r]) => r);
  return larger.length ? larger : null;
}

function findHighlightedRuns(runs: Run[]): Run[] | null {
  const hl = runs.filter((r) => r.font.highlightColor !== null);
  return hl.length ? hl : null;
}

function findNumberSequence(paragraph: Paragraph): Run[] | null {
  const acc: Run[] = [];
  for (const run of paragraph.runs) {
    acc.push(run);
    if (/\d/.test(run.text)) return acc;
  }
  return null;
}

// ── process_document_styles ──────────────────────────────────────────

function processDocumentStyles(doc: OoxmlDoc): void {
  const toRemove: ReturnType<OoxmlDoc['styles']['all']> = [];
  for (const style of doc.styles.all()) {
    const sid = style.styleId;
    const name = style.name;
    if (sid === null || name === null) continue;
    if (Object.prototype.hasOwnProperty.call(COMBINED_STYLE_MAP, sid)) {
      const target = COMBINED_STYLE_MAP[sid]!;
      if (name !== target.name) style.name = target.name;
      if (target.alias) style.setAlias(target.alias);
      else if (style.getAlias() !== null) style.removeAlias();
    } else {
      toRemove.push(style);
    }
  }
  for (const style of toRemove) style.remove();
}

// ── attempt_text_conversion ──────────────────────────────────────────

function attemptTextConversion(
  doc: OoxmlDoc,
  convertAnalytics: boolean,
  progressCallback?: (current: number, total: number) => void,
): void {
  verifyStyleAvailability(doc);

  const citationStyle = getStyleVariation(doc, 'Style13ptBold');
  const underlineStyle = getStyleVariation(doc, 'StyleUnderline');
  const emphasisStyle = getStyleVariation(doc, 'Emphasis');

  const processEntirelyBoldParagraph = (paragraph: Paragraph): boolean => {
    const boldRuns = checkEntirelyBold(paragraph);
    if (!boldRuns) return false;
    const cs = getStyleVariation(doc, 'Style13ptBold');

    const paraText = paragraph.text.trim();
    if (paraText.length <= 60) {
      for (const r of boldRuns) {
        r.style = doc.styles.get(cs);
        r.clearFormatting('always');
      }
      return true;
    }

    const larger = findFontSizeVariation(boldRuns);
    if (larger) {
      const set = new Set(larger);
      for (const r of boldRuns) {
        r.style = set.has(r) ? doc.styles.get(cs) : null;
        r.clearFormatting('always');
      }
      return true;
    }

    const highlighted = findHighlightedRuns(boldRuns);
    if (highlighted) {
      const set = new Set(highlighted);
      for (const r of boldRuns) {
        r.style = set.has(r) ? doc.styles.get(cs) : null;
        r.clearFormatting('always');
      }
      return true;
    }

    // Fresh `paragraph.runs` → no identity overlap with boldRuns (faithful
    // to the Python: every run ends up cleared with no citation style).
    const numberRuns = findNumberSequence(paragraph);
    if (numberRuns) {
      const set = new Set(numberRuns);
      for (const r of boldRuns) {
        r.style = set.has(r) ? doc.styles.get(cs) : null;
        r.clearFormatting('always');
      }
      return true;
    }

    for (const r of boldRuns) {
      r.style = doc.styles.get(cs);
      r.clearFormatting('always');
    }
    return true;
  };

  // ----- First pass: header detection -----
  for (const paragraph of doc.paragraphs) {
    const outline = paragraph.outlineLevel;
    if (outline === 0 && paragraph.runs.some((r) => r.bold === true && r.font.sizePt === 26)) {
      paragraph.style = doc.styles.get('Heading1');
    } else if (outline === 1 && paragraph.runs.some((r) => r.bold === true && r.font.sizePt === 22)) {
      paragraph.style = doc.styles.get('Heading2');
    } else if (
      outline === 2 &&
      paragraph.runs.some((r) => r.bold === true && r.underline === true && r.font.sizePt === 16)
    ) {
      paragraph.style = doc.styles.get('Heading3');
    } else if (outline === 3) {
      const nm = paragraph.style.name;
      if (convertAnalytics && nm !== null && nm.includes('Analytic')) {
        try {
          paragraph.style = doc.styles.get('Analytic');
        } catch {
          paragraph.style = doc.styles.get('Heading4');
        }
      } else if (paragraph.runs.some((r) => r.bold === true)) {
        // python: `r.bold and r.font.color` — font.color is always truthy.
        paragraph.style = doc.styles.get('Heading4');
      }
    } else if (
      convertAnalytics &&
      paragraph.style.name !== null &&
      paragraph.style.name.includes('Analytic')
    ) {
      try {
        paragraph.style = doc.styles.get('Analytic');
      } catch {
        paragraph.style = doc.styles.get('Heading4');
      }
    }
  }

  // ----- Remove unapproved (type==2 / character) styles not in the map -----
  const paraStylesToRemove = doc.styles.all().filter((style) => {
    if (style.type !== 2) return false;
    const sid = style.styleId;
    return sid === null || !Object.prototype.hasOwnProperty.call(COMBINED_STYLE_MAP, sid);
  });
  for (const style of paraStylesToRemove) style.remove();

  // ----- Second pass: run-level processing -----
  let currentSectionHasUnderline = false;
  let afterHeadingSeekingText = false;
  let canProcessCitations = false;

  let totalRuns = 0;
  if (progressCallback) for (const p of doc.paragraphs) totalRuns += p.runs.length;
  let runsProcessed = 0;

  for (const paragraph of doc.paragraphs) {
    const styleName = paragraph.style.name ?? '';
    const isHeading = styleName.startsWith('Heading') || styleName.startsWith('Analytic');
    if (isHeading) {
      currentSectionHasUnderline = false;
      afterHeadingSeekingText = true;
      canProcessCitations = false;
      continue;
    }

    if (!isHeading && afterHeadingSeekingText) {
      const hasText = paragraphHasText(paragraph);
      const isUndertag = styleName.startsWith('Undertag');
      if (hasText && !isUndertag) {
        canProcessCitations = true;
        afterHeadingSeekingText = false;
      } else {
        continue;
      }
    } else {
      canProcessCitations = false;
    }

    for (const run of paragraph.runs) {
      if (run.realUnderline() && !run.realBold()) {
        currentSectionHasUnderline = true;
        break;
      }
    }

    let entirelyBoldDone = false;
    for (const run of paragraph.runs) {
      if (progressCallback) {
        runsProcessed++;
        if (runsProcessed % 200 === 0 || runsProcessed === totalRuns) {
          progressCallback(runsProcessed, totalRuns);
        }
      }

      // Calibri Light / Title style → Underline
      const sn = run.style.name;
      if (!canProcessCitations && sn !== null && sn.includes('Title')) {
        run.style = doc.styles.get(underlineStyle);
        run.clearFormatting('conditional');
        continue;
      }

      // Borders → Emphasis
      if (run.hasBorder() || run.style.hasBorder()) {
        run.style = doc.styles.get(emphasisStyle);
        run.removeBorders();
        run.clearFormatting('skip');
        continue;
      }

      // Citation style used in the wrong place
      if (run.style.name === citationStyle) {
        if (!canProcessCitations && !run.realUnderline()) {
          if (run.font.highlightColor !== null) run.style = doc.styles.get(underlineStyle);
          else run.style = null;
          run.clearFormatting('conditional');
          continue;
        }
      }

      // Bold-off override drops a stale citation style
      if (
        (run.style.name === citationStyle || run.style.name === 'Style 13 pt Bold') &&
        run.isBoldOff()
      ) {
        run.style = null;
      }

      const isUnderlined = run.realUnderline();
      const isBold = run.realBold();

      if (canProcessCitations) {
        if (!entirelyBoldDone) {
          if (processEntirelyBoldParagraph(paragraph)) {
            entirelyBoldDone = true;
            break;
          }
        }
        if (isBold && !(run.style.name === underlineStyle || run.style.name === emphasisStyle)) {
          run.style = doc.styles.get(citationStyle);
          run.clearFormatting('always');
          continue;
        }
      }

      if (
        isUnderlined &&
        !isBold &&
        !(run.style.name === emphasisStyle || run.style.name === citationStyle)
      ) {
        run.style = doc.styles.get(underlineStyle);
      } else if (isBold && isUnderlined) {
        run.style = currentSectionHasUnderline
          ? doc.styles.get(emphasisStyle)
          : doc.styles.get(underlineStyle);
      }

      run.clearFormatting('conditional');
    }
  }

  // ----- Concluding sweep 1: highlighted Normal/unstyled → Underline -----
  for (const paragraph of doc.paragraphs) {
    for (const run of paragraph.runs) {
      if (run.font.highlightColor !== null) {
        const nm = run.style.name;
        if (nm === null || nm === 'Normal' || nm === 'Default Paragraph Font') {
          run.style = doc.styles.get(underlineStyle);
        }
      }
    }
  }

  // ----- Concluding sweep 2: clear <=7pt size from non-Normal styled runs ---
  for (const paragraph of doc.paragraphs) {
    for (const run of paragraph.runs) {
      const nm = run.style.name;
      if (nm !== null && nm !== 'Normal' && nm !== 'Default Paragraph Font') {
        const sp = run.font.sizePt;
        if (sp !== null && sp <= 7) run.clearSize();
      }
    }
  }

  // ----- Final cleanup: clear font name + remove paragraph spacing/ind/jc ---
  for (const paragraph of doc.paragraphs) {
    for (const run of paragraph.runs) run.clearName();
    paragraph.removeParagraphFormatting();
  }

  // ----- Remove hyperlinks (unwrap, keeping their runs) -----
  for (const hl of doc.hyperlinks()) {
    const parent = hl.parentNode;
    if (!parent) continue;
    while (hl.firstChild) parent.insertBefore(hl.firstChild, hl);
    parent.removeChild(hl);
  }
}

// ── Public API: clean_document_bytes ─────────────────────────────────

export interface CleanOptions {
  /** Strip unreferenced style definitions before and after cleaning. */
  pruneUnused?: boolean;
  /** Called with (runsProcessed, totalRuns) during the conversion pass. */
  progressCallback?: (current: number, total: number) => void;
}

export async function cleanDocumentBytes(
  fileBytes: Uint8Array,
  options: CleanOptions = {},
): Promise<Uint8Array> {
  const pruneUnused = options.pruneUnused ?? false;

  let bytes = fileBytes;
  if (pruneUnused) bytes = (await pruneUnusedStyles(bytes)).bytes;

  const docx = await Docx.load(bytes);
  const doc = await OoxmlDoc.fromDocx(docx);

  normalizeStyleDefinitions(doc);
  attemptTextConversion(doc, true, options.progressCallback);
  processDocumentStyles(doc);

  let result = await doc.save();

  if (pruneUnused) result = (await pruneUnusedStyles(result)).bytes;
  result = (await fixDanglingStyleRefs(result)).bytes;
  return result;
}
