/**
 * Export public API: schema doc → .docx bytes.
 */

import type { Node as PMNode } from 'prosemirror-model';
import { Docx } from '../ooxml/docx.js';
import { exportDoc } from './exporter.js';

export { exportDoc } from './exporter.js';
export type { ExportResult } from './exporter.js';

/**
 * Serialize a ProseMirror doc to a complete .docx byte buffer, ready
 * to write to disk or send across a wire. Image nodes contribute
 * media parts (binary writes under `word/media/`) tracked alongside
 * the document XML.
 */
export async function toDocx(doc: PMNode): Promise<Uint8Array> {
  const result = exportDoc(doc);
  const docx = Docx.empty();
  docx.writeText('word/document.xml', result.documentXml);
  docx.writeText('word/_rels/document.xml.rels', result.relsXml);
  for (const part of result.mediaParts) {
    docx.writeBinary(part.path, part.bytes);
  }
  return docx.toBuffer();
}
