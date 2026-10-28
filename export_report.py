"""
=============================================================================
export_report.py
-----------------------------------------------------------------------------
Generates formal, publication-grade document reports for the
E-Commerce Customer 360 & Predictive Analytics Project:

1. PROJECT_REPORT.docx - Native Microsoft Word document (ECMA-376 OpenXML)
2. PROJECT_REPORT.html - Self-contained, print-ready HTML/PDF report
=============================================================================
"""

import sys
import os
import io
import base64
import zipfile
import html
from pathlib import Path
from PIL import Image

# Ensure standard UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
DOCS_DIR = PROJECT_ROOT / "docs"
ARCH_IMG_PATH = DOCS_DIR / "architecture_flow.png"
SCHEMA_IMG_PATH = DOCS_DIR / "database_schema.png"
OUTPUT_DOCX = PROJECT_ROOT / "PROJECT_REPORT.docx"
OUTPUT_HTML = PROJECT_ROOT / "PROJECT_REPORT.html"


def escape_xml(s: str) -> str:
    """Escapes special characters for XML."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))


class DocxBuilder:
    """Builds a rich, standard-compliant Microsoft Word (.docx) file."""

    def __init__(self):
        self.paragraphs = []
        self.relationships = []
        self.rel_id_counter = 1
        self.media_files = {}  # target_filename -> bytes

    def add_relationship(self, rel_type: str, target: str) -> str:
        r_id = f"rId{self.rel_id_counter}"
        self.rel_id_counter += 1
        self.relationships.append((r_id, rel_type, target))
        return r_id

    def add_title(self, text: str, subtitle: str = ""):
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="360" w:after="120"/>
            <w:jc w:val="center"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
              <w:b/>
              <w:sz w:val="56"/>
              <w:color w:val="0F172A"/>
            </w:rPr>
            <w:t>{escape_xml(text)}</w:t>
          </w:r>
        </w:p>
        """
        if subtitle:
            xml += f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="60" w:after="360"/>
                <w:jc w:val="center"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
                  <w:i/>
                  <w:sz w:val="26"/>
                  <w:color w:val="475569"/>
                </w:rPr>
                <w:t>{escape_xml(subtitle)}</w:t>
              </w:r>
            </w:p>
            """
        self.paragraphs.append(xml)

    def add_metadata_box(self, items: list):
        """Adds a neat metadata table at the top of the report."""
        rows_xml = ""
        for key, val in items:
            rows_xml += f"""
            <w:tr>
              <w:tc>
                <w:tcPr>
                  <w:tcW w:w="3000" w:type="dxa"/>
                  <w:shd w:val="clear" w:color="auto" w:fill="F8FAFC"/>
                </w:tcPr>
                <w:p>
                  <w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>
                  <w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="1E293B"/></w:rPr><w:t>{escape_xml(key)}</w:t></w:r>
                </w:p>
              </w:tc>
              <w:tc>
                <w:tcPr>
                  <w:tcW w:w="6360" w:type="dxa"/>
                  <w:shd w:val="clear" w:color="auto" w:fill="FFFFFF"/>
                </w:tcPr>
                <w:p>
                  <w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>
                  <w:r><w:rPr><w:sz w:val="20"/><w:color w:val="334155"/></w:rPr><w:t>{escape_xml(val)}</w:t></w:r>
                </w:p>
              </w:tc>
            </w:tr>
            """
        tbl_xml = f"""
        <w:tbl>
          <w:tblPr>
            <w:tblW w:w="9360" w:type="dxa"/>
            <w:jc w:val="center"/>
            <w:tblBorders>
              <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
              <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
            </w:tblBorders>
            <w:tblCellMar>
              <w:top w:w="120" w:type="dxa"/>
              <w:bottom w:w="120" w:type="dxa"/>
              <w:left w:w="180" w:type="dxa"/>
              <w:right w:w="180" w:type="dxa"/>
            </w:tblCellMar>
          </w:tblPr>
          {rows_xml}
        </w:tbl>
        <w:p><w:pPr><w:spacing w:before="180" w:after="180"/></w:pPr></w:p>
        """
        self.paragraphs.append(tbl_xml)

    def add_h1(self, text: str):
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="400" w:after="140"/>
            <w:keepNext/>
            <w:pBdr>
              <w:bottom w:val="single" w:sz="12" w:space="4" w:color="2563EB"/>
            </w:pBdr>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
              <w:b/>
              <w:sz w:val="36"/>
              <w:color w:val="1E3A8A"/>
            </w:rPr>
            <w:t>{escape_xml(text)}</w:t>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_h2(self, text: str):
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="280" w:after="100"/>
            <w:keepNext/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
              <w:b/>
              <w:sz w:val="28"/>
              <w:color w:val="2563EB"/>
            </w:rPr>
            <w:t>{escape_xml(text)}</w:t>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_h3(self, text: str):
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="200" w:after="80"/>
            <w:keepNext/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
              <w:b/>
              <w:sz w:val="24"/>
              <w:color w:val="0F172A"/>
            </w:rPr>
            <w:t>{escape_xml(text)}</w:t>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_p(self, text: str, bold_prefix: str = "", italic: bool = False):
        runs = ""
        if bold_prefix:
            runs += f"""
            <w:r>
              <w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="0F172A"/></w:rPr>
              <w:t xml:space="preserve">{escape_xml(bold_prefix)} </w:t>
            </w:r>
            """
        i_tag = "<w:i/>" if italic else ""
        runs += f"""
        <w:r>
          <w:rPr>{i_tag}<w:sz w:val="22"/><w:color w:val="334155"/></w:rPr>
          <w:t>{escape_xml(text)}</w:t>
        </w:r>
        """
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="60" w:after="100"/>
            <w:line w:line="276" w:lineRule="auto"/>
          </w:pPr>
          {runs}
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_bullet(self, bold_prefix: str, text: str):
        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="40" w:after="60"/>
            <w:ind w:left="480" w:hanging="240"/>
          </w:pPr>
          <w:r>
            <w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/><w:sz w:val="20"/><w:color w:val="2563EB"/></w:rPr>
            <w:t>•   </w:t>
          </w:r>
          <w:r>
            <w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="0F172A"/></w:rPr>
            <w:t xml:space="preserve">{escape_xml(bold_prefix)}: </w:t>
          </w:r>
          <w:r>
            <w:rPr><w:sz w:val="22"/><w:color w:val="334155"/></w:rPr>
            <w:t>{escape_xml(text)}</w:t>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_callout(self, title: str, text: str):
        xml = f"""
        <w:tbl>
          <w:tblPr>
            <w:tblW w:w="9360" w:type="dxa"/>
            <w:jc w:val="center"/>
            <w:tblBorders>
              <w:top w:val="none"/>
              <w:left w:val="single" w:sz="24" w:space="0" w:color="2563EB"/>
              <w:bottom w:val="none"/>
              <w:right w:val="none"/>
              <w:insideH w:val="none"/>
              <w:insideV w:val="none"/>
            </w:tblBorders>
            <w:tblCellMar>
              <w:top w:w="140" w:type="dxa"/>
              <w:bottom w:w="140" w:type="dxa"/>
              <w:left w:w="220" w:type="dxa"/>
              <w:right w:w="220" w:type="dxa"/>
            </w:tblCellMar>
          </w:tblPr>
          <w:tr>
            <w:tc>
              <w:tcPr>
                <w:tcW w:w="9360" w:type="dxa"/>
                <w:shd w:val="clear" w:color="auto" w:fill="EFF6FF"/>
              </w:tcPr>
              <w:p>
                <w:pPr><w:spacing w:before="60" w:after="40"/></w:pPr>
                <w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="1E3A8A"/></w:rPr><w:t>{escape_xml(title)}</w:t></w:r>
              </w:p>
              <w:p>
                <w:pPr><w:spacing w:before="20" w:after="60"/></w:pPr>
                <w:r><w:rPr><w:sz w:val="20"/><w:color w:val="1E293B"/></w:rPr><w:t>{escape_xml(text)}</w:t></w:r>
              </w:p>
            </w:tc>
          </w:tr>
        </w:tbl>
        <w:p><w:pPr><w:spacing w:before="80" w:after="120"/></w:pPr></w:p>
        """
        self.paragraphs.append(xml)

    def add_table(self, headers: list, rows: list, col_widths: list = None):
        if col_widths is None:
            total_w = 9360
            each_w = int(total_w / len(headers))
            col_widths = [each_w] * len(headers)

        header_xml = "<w:tr><w:trPr><w:tblHeader/></w:trPr>"
        for i, h in enumerate(headers):
            w = col_widths[i]
            header_xml += f"""
            <w:tc>
              <w:tcPr>
                <w:tcW w:w="{w}" w:type="dxa"/>
                <w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/>
              </w:tcPr>
              <w:p>
                <w:pPr><w:spacing w:before="100" w:after="100"/><w:jc w:val="center"/></w:pPr>
                <w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="FFFFFF"/></w:rPr><w:t>{escape_xml(h)}</w:t></w:r>
              </w:p>
            </w:tc>
            """
        header_xml += "</w:tr>"

        rows_xml = ""
        for r_idx, row in enumerate(rows):
            bg = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
            rows_xml += "<w:tr>"
            for c_idx, cell in enumerate(row):
                w = col_widths[c_idx]
                align = "center" if c_idx == 0 or len(str(cell)) < 12 else "left"
                rows_xml += f"""
                <w:tc>
                  <w:tcPr>
                    <w:tcW w:w="{w}" w:type="dxa"/>
                    <w:shd w:val="clear" w:color="auto" w:fill="{bg}"/>
                  </w:tcPr>
                  <w:p>
                    <w:pPr><w:spacing w:before="80" w:after="80"/><w:jc w:val="{align}"/></w:pPr>
                    <w:r><w:rPr><w:sz w:val="20"/><w:color w:val="334155"/></w:rPr><w:t>{escape_xml(str(cell))}</w:t></w:r>
                  </w:p>
                </w:tc>
                """
            rows_xml += "</w:tr>"

        tbl_xml = f"""
        <w:tbl>
          <w:tblPr>
            <w:tblW w:w="9360" w:type="dxa"/>
            <w:jc w:val="center"/>
            <w:tblBorders>
              <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
              <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
              <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
            </w:tblBorders>
            <w:tblCellMar>
              <w:top w:w="100" w:type="dxa"/>
              <w:bottom w:w="100" w:type="dxa"/>
              <w:left w:w="140" w:type="dxa"/>
              <w:right w:w="140" w:type="dxa"/>
            </w:tblCellMar>
          </w:tblPr>
          {header_xml}
          {rows_xml}
        </w:tbl>
        <w:p><w:pPr><w:spacing w:before="120" w:after="160"/></w:pPr></w:p>
        """
        self.paragraphs.append(tbl_xml)

    def add_code(self, code_text: str):
        lines = code_text.strip().split("\n")
        p_lines = ""
        for line in lines:
            p_lines += f"""
            <w:p>
              <w:pPr>
                <w:spacing w:before="20" w:after="20"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>
                  <w:sz w:val="18"/>
                  <w:color w:val="0F172A"/>
                </w:rPr>
                <w:t xml:space="preserve">{escape_xml(line)}</w:t>
              </w:r>
            </w:p>
            """
        xml = f"""
        <w:tbl>
          <w:tblPr>
            <w:tblW w:w="9360" w:type="dxa"/>
            <w:jc w:val="center"/>
            <w:tblBorders>
              <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
              <w:left w:val="single" w:sz="16" w:space="0" w:color="3B82F6"/>
              <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
              <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
              <w:insideH w:val="none"/>
              <w:insideV w:val="none"/>
            </w:tblBorders>
            <w:tblCellMar>
              <w:top w:w="120" w:type="dxa"/>
              <w:bottom w:w="120" w:type="dxa"/>
              <w:left w:w="180" w:type="dxa"/>
              <w:right w:w="180" w:type="dxa"/>
            </w:tblCellMar>
          </w:tblPr>
          <w:tr>
            <w:tc>
              <w:tcPr>
                <w:tcW w:w="9360" w:type="dxa"/>
                <w:shd w:val="clear" w:color="auto" w:fill="F8FAFC"/>
              </w:tcPr>
              {p_lines}
            </w:tc>
          </w:tr>
        </w:tbl>
        <w:p><w:pPr><w:spacing w:before="80" w:after="140"/></w:pPr></w:p>
        """
        self.paragraphs.append(xml)

    def add_image(self, img_path: Path, caption: str):
        if not img_path.exists():
            return
        with open(img_path, "rb") as f:
            img_data = f.read()

        with Image.open(img_path) as im:
            w, h = im.size

        max_w_emu = 5760000  # 6.3 inches
        cx = max_w_emu
        cy = int(max_w_emu * (h / w))

        img_filename = f"image_{self.rel_id_counter}.png"
        r_id = self.add_relationship(
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            f"media/{img_filename}"
        )
        self.media_files[img_filename] = img_data

        xml = f"""
        <w:p>
          <w:pPr>
            <w:spacing w:before="140" w:after="60"/>
            <w:jc w:val="center"/>
          </w:pPr>
          <w:r>
            <w:drawing>
              <wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
                <wp:extent cx="{cx}" cy="{cy}"/>
                <wp:effectExtent l="0" t="0" r="0" b="0"/>
                <wp:docPr id="{self.rel_id_counter}" name="{escape_xml(caption)}"/>
                <wp:cNvGraphicFramePr>
                  <a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>
                </wp:cNvGraphicFramePr>
                <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                  <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                    <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                      <pic:nvPicPr>
                        <pic:cNvPr id="0" name="{escape_xml(caption)}"/>
                        <pic:cNvPicPr/>
                      </pic:nvPicPr>
                      <pic:blipFill>
                        <a:blip r:embed="{r_id}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
                        <a:stretch><a:fillRect/></a:stretch>
                      </pic:blipFill>
                      <pic:spPr>
                        <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                      </pic:spPr>
                    </pic:pic>
                  </a:graphicData>
                </a:graphic>
              </wp:inline>
            </w:drawing>
          </w:r>
        </w:p>
        <w:p>
          <w:pPr>
            <w:spacing w:before="40" w:after="160"/>
            <w:jc w:val="center"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
              <w:i/>
              <w:sz w:val="18"/>
              <w:color w:val="64748B"/>
            </w:rPr>
            <w:t>Figure: {escape_xml(caption)}</w:t>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def add_page_break(self):
        xml = """
        <w:p>
          <w:r>
            <w:br w:type="page"/>
          </w:r>
        </w:p>
        """
        self.paragraphs.append(xml)

    def save(self, filepath: Path):
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

        root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

        doc_rels_items = ""
        for r_id, r_type, target in self.relationships:
            doc_rels_items += f'<Relationship Id="{r_id}" Type="{r_type}" Target="{target}"/>\n'
        doc_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {doc_rels_items}
</Relationships>"""

        styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="334155"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>"""

        body_content = "\n".join(self.paragraphs)
        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {body_content}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

        temp_path = filepath.with_suffix(".tmp.docx")
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types)
            z.writestr("_rels/.rels", root_rels)
            z.writestr("word/_rels/document.xml.rels", doc_rels)
            z.writestr("word/styles.xml", styles)
            z.writestr("word/document.xml", document_xml)
            for fname, bdata in self.media_files.items():
                z.writestr(f"word/media/{fname}", bdata)

        if filepath.exists():
            try:
                os.remove(filepath)
            except Exception:
                pass
        os.replace(temp_path, filepath)
        print(f"[OK] Generated DOCX Report: {filepath} ({filepath.stat().st_size:,} bytes)")


def generate_docx():
    """Compiles the formal Microsoft Word document."""
    doc = DocxBuilder()

    # Cover / Header
    doc.add_title(
        "Technical Project Report: E-Commerce Customer 360 & Behavioral Analytics Engine",
        "Document-Oriented Big Data Architecture, In-Database Feature Engineering, and Machine Learning on MongoDB Atlas"
    )

    metadata = [
        ("Project Capstone", "MongoDB Data Science & Behavioral Analytics Platform"),
        ("Database Cluster", "MongoDB Atlas Multi-AZ Cloud Cluster (v8.x)"),
        ("Host / URI", "Configured with the MONGO_URI environment variable"),
        ("Database & Collection", "ecommerce_analytics.customers (WiredTiger Engine)"),
        ("Core Technology Stack", "Python 3.13, PyMongo, Scikit-Learn, XGBoost, Pandas, Streamlit"),
        ("Underlying Dataset", "UCI Online Retail Repository (541,909 Transactions cleansed to 4,338 Customer Profiles)"),
        ("Author & Workspace", r"Aman Garg | Workspace: d:\MongoDB"),
        ("Publication Date", "October 2026"),
    ]
    doc.add_metadata_box(metadata)

    doc.add_callout(
        "Executive Summary & Project Significance",
        "This project architects an enterprise Customer 360 intelligence platform on MongoDB Atlas. By replacing relational "
        "normalized joins with an embedded BSON document structure, query latency is reduced to O(1) point lookups. "
        "Analytical feature extraction (RFM vectors, triangular cohort matrices) is executed entirely within MongoDB's C++ "
        "aggregation engine before feeding an XGBoost churn classifier (ROC-AUC: 0.9558, Accuracy: 87.00%) and a clean, "
        "light-themed interactive Streamlit dashboard."
    )

    # 1. Motivation
    doc.add_h1("1. Problem Statement & Database Architecture Motivation")
    doc.add_p(
        "In traditional e-commerce analytics pipelines powered by relational databases (RDBMS), data is normalized into "
        "third normal form (3NF). Queries requiring a holistic view of customer behavior must join Customers, Orders, "
        "Order_Items, and Products. Across millions of historical records, multi-table nested loop and hash joins cause "
        "severe latency spikes, database locking, and memory exhaustion."
    )
    doc.add_bullet("Normalized RDBMS Joins", "Degrades query performance from milliseconds to tens of seconds at scale.")
    doc.add_bullet("Memory Fragmentation", "Row fragments scattered across multiple disk pages eliminate CPU cache locality.")
    doc.add_bullet("MongoDB Solution", "Embedded Customer 360 documents co-locate all customer orders and purchase items in contiguous memory pages.")
    doc.add_bullet("Single-Document Atomicity", "Customer updates, new purchases, and lifetime stats are committed atomically without 2-phase locks.")

    # 2. Dataset
    doc.add_h1("2. Dataset Exploration & Preprocessing Pipeline")
    doc.add_p(
        "The project utilizes the UCI Online Retail Dataset, comprising 541,909 real transactional records from a UK-based "
        "online retailer specializing in giftware."
    )
    doc.add_bullet("Raw Ingestion Volume", "541,909 rows loaded from Online Retail.xlsx.")
    doc.add_bullet("Null Customer Pruning", "135,080 guest checkouts missing CustomerID were removed.")
    doc.add_bullet("Cancellation Cleansing", "8,905 cancelled orders (invoice codes starting with 'C') or non-positive quantities were filtered out.")
    doc.add_bullet("Clean Purchase Records", "397,884 verified line items across 4,338 unique customers were synthesized into hierarchical Customer 360 profiles.")

    # 3. MongoDB Schema & Governance
    doc.add_h1("3. MongoDB Database Design, $jsonSchema & Index Strategy")
    doc.add_p(
        "The primary data entity is stored in the customers collection in MongoDB Atlas. Collection-level validation is "
        "enforced via $jsonSchema, rejecting any document that does not satisfy required types and subdocument constraints."
    )

    doc.add_code("""// Annotated Customer 360 Document Schema
{
  "_id": ObjectId("67207c4b1234567890abcdef"),
  "customer_id": "17850",
  "country": "United Kingdom",
  "first_purchase_date": ISODate("2010-12-01T08:26:00.000Z"),
  "last_purchase_date": ISODate("2011-02-10T14:38:00.000Z"),
  "total_orders_count": 34,
  "orders": [
    {
      "invoice_no": "536365",
      "invoice_date": ISODate("2010-12-01T08:26:00.000Z"),
      "order_total": 139.12,
      "items_count": 7,
      "items": [
        { "stock_code": "85123A", "description": "WHITE HANGING HEART T-LIGHT HOLDER", "quantity": 6, "unit_price": 2.55, "line_total": 15.30 }
      ]
    }
  ]
}""")

    doc.add_h2("Index Architecture & Query Optimization")
    doc.add_p(
        "To ensure that all analytics, filtering, and single-customer dashboard lookups operate at maximum throughput, "
        "five secondary B-Tree indexes were created:"
    )

    index_headers = ["Index Key", "Type", "Execution Benefit"]
    index_rows = [
        ["{ customer_id: 1 }", "Unique B-Tree", "Enforces business key uniqueness; O(1) point lookups (IXSCAN)"],
        ["{ country: 1 }", "B-Tree", "Accelerates geographic revenue aggregation ($group stage)"],
        ["{ last_purchase_date: 1 }", "B-Tree", "Enables range scans for Recency calculations and churn thresholding"],
        ["{ first_purchase_date: 1 }", "B-Tree", "Optimizes triangular monthly cohort acquisition grouping"],
        ["{ total_orders_count: 1 }", "B-Tree", "High-frequency buyer filtering and VIP segmentation"],
    ]
    doc.add_table(index_headers, index_rows, [2800, 2000, 4560])

    # Diagram 1
    if SCHEMA_IMG_PATH.exists():
        doc.add_image(SCHEMA_IMG_PATH, "MongoDB Customer 360 Entity-Relationship & Document Schema")

    # 4. Aggregations
    doc.add_h1("4. In-Database MongoDB Aggregation Framework")
    doc.add_p(
        "A cornerstone of this architecture is offloading heavy analytical transformations to MongoDB's C++ aggregation engine. "
        "Instead of transferring raw transactional payloads over the network, computed analytical vectors are retrieved directly."
    )

    doc.add_h2("Pipeline 1: In-Engine RFM & Churn Feature Extraction")
    doc.add_p(
        "Calculates Recency (days since snapshot date 2011-12-10), Frequency (total orders), Monetary (sum of order totals), "
        "Average Order Value (AOV), and 90-day Churn ground truth directly inside the database."
    )
    doc.add_code("""db.customers.aggregate([
  {
    $project: {
      customer_id: 1, country: 1,
      frequency: { $size: { $ifNull: ["$orders", []] } },
      monetary: { $round: [{ $sum: "$orders.order_total" }, 2] },
      recency_days: {
        $round: [{ $divide: [{ $subtract: [ISODate("2011-12-10T00:00:00Z"), "$last_purchase_date"] }, 86400000] }, 1]
      }
    }
  },
  {
    $project: {
      customer_id: 1, country: 1, recency_days: 1, frequency: 1, monetary: 1,
      avg_order_value: { $round: [{ $cond: [{ $gt: ["$frequency", 0] }, { $divide: ["$monetary", "$frequency"] }, 0] }, 2] },
      is_churned: { $cond: [{ $gte: ["$recency_days", 90] }, 1, 0] }
    }
  }
]);""")

    doc.add_h2("Pipeline 2: Monthly Triangular Cohort Retention Matrix")
    doc.add_p(
        "Unwinds the embedded orders array, calculates the relative cohort month index for each purchase, and groups "
        "active customer IDs into unique sets ($addToSet) to track retention decay across 12 monthly cohorts."
    )

    # 5. Machine Learning
    doc.add_h1("5. Machine Learning & Predictive Analytics Methodology")

    doc.add_h2("5.1 Unsupervised RFM Customer Segmentation (K-Means)")
    doc.add_p(
        "Customer spend and order frequency exhibit severe right-skewed Pareto distributions. Features were log-transformed "
        "ln(1 + x) and standardized using StandardScaler. K-Means clustering was executed with k=4, achieving an optimal "
        "Silhouette Score of 0.337."
    )

    cluster_headers = ["Cluster ID", "Mean Recency", "Mean Frequency", "Mean Spend (£)", "Assigned Persona Profile"]
    cluster_rows = [
        ["0", "180.4 days", "1.3 orders", "£341.30", "Dormant / One-Time Buyers"],
        ["1", "11.5 days", "13.8 orders", "£8,133.60", "Champions & VIP Super-Users"],
        ["2", "17.2 days", "2.2 orders", "£560.20", "Active Standard Shoppers"],
        ["3", "70.9 days", "4.1 orders", "£1,811.50", "Mid-Tier Maturing Accounts"],
    ]
    doc.add_table(cluster_headers, cluster_rows, [1400, 1800, 1800, 1800, 2560])

    doc.add_h2("5.2 Supervised Churn Classification (XGBoost)")
    doc.add_p(
        "A critical methodology safeguard was enforced: recency_days was strictly excluded from training features to "
        "prevent target leakage (since churn is defined as recency >= 90 days). Training was performed using XGBoost "
        "with scale_pos_weight=1.99 to account for class imbalance (2,166 active vs 1,087 churned in training cohort)."
    )

    doc.add_h3("Model Diagnostic Scorecard (Stratified Test Set, n=1,085):")
    metric_headers = ["Evaluation Metric", "Experimental Score", "Industry Benchmark / Status"]
    metric_rows = [
        ["ROC-AUC", "0.9558", "Outstanding discriminative power (> 0.90 is gold standard)"],
        ["PR-AUC (Avg Precision)", "0.9292", "High precision maintained under class imbalance"],
        ["Overall Accuracy", "87.00%", "Reliable prediction across active and churning accounts"],
        ["F1-Score", "0.8190", "Harmonious balance between Precision (76.5%) and Recall (88.1%)"],
    ]
    doc.add_table(metric_headers, metric_rows, [2800, 2200, 4360])

    doc.add_h3("Confusion Matrix Evaluation:")
    cm_headers = ["Actual Class", "Predicted Active", "Predicted Churned", "Class Recall"]
    cm_rows = [
        ["Actual Active (Negative)", "625 (True Neg)", "98 (False Pos)", "86.4% Specificity"],
        ["Actual Churned (Positive)", "43 (False Neg)", "319 (True Pos)", "88.1% Sensitivity / Recall"],
    ]
    doc.add_table(cm_headers, cm_rows, [2800, 2200, 2200, 2160])

    # Diagram 2
    if ARCH_IMG_PATH.exists():
        doc.add_image(ARCH_IMG_PATH, "End-to-End System Architecture & Data Flow")

    # 6. Interactive Presentation Tier
    doc.add_h1("6. Interactive Web Presentation Tier (Streamlit)")
    doc.add_p(
        "An enterprise-ready light-themed dashboard was built using Streamlit (app/dashboard.py) with customized typography "
        "and clean white/slate styling (.streamlit/config.toml), eliminating dark/cyberpunk UI aesthetics."
    )
    doc.add_bullet("Tab 1: Overview & Market KPIs", "Active customer counts (4,338), gross revenue (£8.91M), average CLV (£2,054), and regional sales charts.")
    doc.add_bullet("Tab 2: Customer Personas", "RFM quartile breakdown, 2D interactive scatter plot (Recency vs Monetary), and strategic marketing playbook.")
    doc.add_bullet("Tab 3: Cohort Retention", "Interactive triangular retention heatmap visualizing monthly decay across acquisition cohorts.")
    doc.add_bullet("Tab 4: Customer 360 Lookup", "Instant point query lookup by CustomerID showing lifetime history, nested order details, and an animated radial churn risk gauge.")

    # 7. Business Insights
    doc.add_h1("7. Business Insights & Strategic Action Playbook")
    doc.add_bullet("Pareto Revenue Skew", "Top 10.4% of customers (Cluster 1 VIPs) drive 58% of total gross revenue. Preserving these VIP accounts is paramount.")
    doc.add_bullet("Crucial Retention Window", "Retention drops steeply from Month 1 (100%) to Month 2 (28%). Marketing automation must trigger onboarding drips within 14-21 days of first order.")
    doc.add_bullet("European Basket Sizes", "While the UK represents 82% of gross revenue, European markets (Netherlands, Germany, EIRE) display 2.4x higher average order values.")

    # 8. Execution Guide
    doc.add_h1("8. Verification & CLI Execution Guide")
    doc.add_p(
        r"The complete platform is fully self-contained in d:\MongoDB and can be launched with a single click or CLI command:"
    )
    doc.add_code(r"""# Option A: 1-Click Launch (Windows Explorer)
Double-click: run_dashboard.bat

# Option B: Terminal Command (PowerShell)
cd d:\MongoDB
.\.venv\Scripts\streamlit.exe run app/dashboard.py

# Option C: Re-run Full ETL Ingestion & Model Training
.\.venv\Scripts\python.exe main.py""")

    doc.save(OUTPUT_DOCX)


def generate_html():
    """Generates a self-contained, publication-ready HTML/PDF report."""
    arch_b64 = ""
    schema_b64 = ""
    if ARCH_IMG_PATH.exists():
        with open(ARCH_IMG_PATH, "rb") as f:
            arch_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    if SCHEMA_IMG_PATH.exists():
        with open(SCHEMA_IMG_PATH, "rb") as f:
            schema_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Project Report - E-Commerce Customer 360 & Predictive Analytics</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm;
      @bottom-right {{
        content: counter(page);
      }}
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      background-color: #f8fafc;
      line-height: 1.6;
      margin: 0;
      padding: 0;
    }}
    .document-container {{
      max-width: 960px;
      margin: 30px auto;
      background: #ffffff;
      padding: 50px 60px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border-radius: 8px;
    }}
    @media print {{
      body {{ background: #ffffff; }}
      .document-container {{
        box-shadow: none;
        padding: 0;
        margin: 0;
        max-width: 100%;
      }}
      .no-print {{ display: none; }}
      .page-break {{ page-break-before: always; }}
    }}
    h1.report-title {{
      font-size: 28pt;
      font-weight: 800;
      color: #0f172a;
      line-height: 1.2;
      margin-bottom: 8px;
      text-align: center;
    }}
    p.report-subtitle {{
      font-size: 13pt;
      color: #475569;
      text-align: center;
      margin-top: 0;
      margin-bottom: 30px;
      font-style: italic;
    }}
    .meta-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 30px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      overflow: hidden;
    }}
    .meta-table td {{
      padding: 10px 14px;
      font-size: 10.5pt;
      border-bottom: 1px solid #e2e8f0;
    }}
    .meta-table td.label {{
      font-weight: 700;
      color: #1e293b;
      background-color: #f1f5f9;
      width: 28%;
    }}
    .callout {{
      background-color: #eff6ff;
      border-left: 4px solid #2563eb;
      padding: 16px 20px;
      border-radius: 0 6px 6px 0;
      margin: 25px 0;
    }}
    .callout h4 {{
      margin: 0 0 6px 0;
      color: #1e3a8a;
      font-size: 12pt;
    }}
    .callout p {{
      margin: 0;
      font-size: 10.5pt;
      color: #1e293b;
    }}
    h2.section-heading {{
      font-size: 16pt;
      font-weight: 700;
      color: #1e3a8a;
      border-bottom: 2px solid #2563eb;
      padding-bottom: 6px;
      margin-top: 35px;
      margin-bottom: 15px;
    }}
    h3.sub-heading {{
      font-size: 13pt;
      font-weight: 600;
      color: #2563eb;
      margin-top: 25px;
      margin-bottom: 10px;
    }}
    p, li {{
      font-size: 11pt;
      color: #334155;
    }}
    ul {{
      margin-top: 8px;
      margin-bottom: 15px;
      padding-left: 24px;
    }}
    li {{
      margin-bottom: 6px;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 10.5pt;
    }}
    .data-table th {{
      background-color: #1e3a8a;
      color: #ffffff;
      padding: 10px 12px;
      font-weight: 600;
      border: 1px solid #cbd5e1;
      text-align: left;
    }}
    .data-table td {{
      padding: 9px 12px;
      border: 1px solid #e2e8f0;
      color: #334155;
    }}
    .data-table tr:nth-child(even) td {{
      background-color: #f8fafc;
    }}
    pre.code-block {{
      background-color: #0f172a;
      color: #f1f5f9;
      padding: 16px;
      border-radius: 6px;
      font-family: Consolas, Monaco, "Courier New", monospace;
      font-size: 9.5pt;
      line-height: 1.45;
      overflow-x: auto;
      margin: 18px 0;
    }}
    .figure-container {{
      text-align: center;
      margin: 30px 0;
    }}
    .figure-container img {{
      max-width: 100%;
      height: auto;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }}
    .figure-caption {{
      font-size: 10pt;
      color: #64748b;
      margin-top: 8px;
      font-style: italic;
    }}
    .action-bar {{
      position: sticky;
      top: 15px;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-bottom: 15px;
      z-index: 100;
    }}
    .btn {{
      background-color: #2563eb;
      color: white;
      border: none;
      padding: 10px 18px;
      border-radius: 6px;
      font-size: 10pt;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
      text-decoration: none;
    }}
    .btn:hover {{
      background-color: #1d4ed8;
    }}
    .btn-secondary {{
      background-color: #475569;
    }}
    .btn-secondary:hover {{
      background-color: #334155;
    }}
  </style>
</head>
<body>

  <div class="document-container">
    <div class="action-bar no-print">
      <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
      <a class="btn btn-secondary" href="PROJECT_REPORT.docx" download>📥 Download Word (.docx)</a>
    </div>

    <h1 class="report-title">Technical Project Report</h1>
    <p class="report-subtitle">E-Commerce Customer 360 & Behavioral Analytics Engine on MongoDB Atlas</p>

    <table class="meta-table">
      <tr>
        <td class="label">Project Title</td>
        <td><strong>E-Commerce Customer 360° & Predictive Churn / RFM Analytics Platform</strong></td>
      </tr>
      <tr>
        <td class="label">Database Cluster</td>
        <td>MongoDB connection configured via the <code>MONGO_URI</code> environment variable</td>
      </tr>
      <tr>
        <td class="label">Database & Collection</td>
        <td><code>ecommerce_analytics.customers</code> (4,338 Customer 360 Documents)</td>
      </tr>
      <tr>
        <td class="label">Tech Stack</td>
        <td>Python 3.13, PyMongo, Scikit-Learn, XGBoost, Pandas, Plotly, Streamlit</td>
      </tr>
      <tr>
        <td class="label">Source Dataset</td>
        <td>UCI Online Retail Dataset (541,909 raw records &rarr; 397,884 verified purchase lines)</td>
      </tr>
      <tr>
        <td class="label">Developer & Workspace</td>
        <td>Aman Garg &bull; Workspace: <code>d:\\MongoDB</code></td>
      </tr>
      <tr>
        <td class="label">Date</td>
        <td>October 2026</td>
      </tr>
    </table>

    <div class="callout">
      <h4>Executive Summary & Core Achievement</h4>
      <p>This report documents the design, implementation, and deployment of a full-stack Customer 360 predictive analytics platform. By modeling customer purchasing history into hierarchical BSON documents, relational multi-table JOIN latency is eliminated. In-database feature engineering is offloaded entirely to MongoDB's C++ aggregation engine before feeding machine learning models (XGBoost Churn Classifier ROC-AUC: <strong>0.9558</strong>, Accuracy: <strong>87.00%</strong>; K-Means Silhouette Score: <strong>0.337</strong>). The platform is monitored through a clean, light-themed Streamlit dashboard.</p>
    </div>

    <h2 class="section-heading">1. Problem Statement & Database Architecture Motivation</h2>
    <p>In traditional third-normal-form (3NF) relational architectures, customer order history is partitioned across separate tables (<code>Customers</code>, <code>Orders</code>, <code>Order_Items</code>, <code>Products</code>). As transaction volume scales into millions of rows, analytical queries face critical bottlenecks:</p>
    <ul>
      <li><strong>Degraded Join Latency:</strong> Multi-table nested loop and hash joins cause queries to degrade from milliseconds to tens of seconds.</li>
      <li><strong>Memory Fragmentation:</strong> Relational rows are stored across separate disk blocks, eliminating CPU cache locality.</li>
      <li><strong>MongoDB Document Solution:</strong> By embedding orders and item arrays inside the root customer document, all data pertaining to a customer is co-located in contiguous memory pages, enabling <strong>O(1) indexed point lookups</strong>.</li>
      <li><strong>Single-Document Atomicity:</strong> Updates to customer order history and cumulative stats commit atomically without the overhead of distributed two-phase locking.</li>
    </ul>

    <h2 class="section-heading">2. Dataset Overview & Cleansing Pipeline</h2>
    <p>The system ingests the UCI Machine Learning Online Retail Dataset, comprising real purchases from a UK-based giftware merchant.</p>
    <ul>
      <li><strong>Raw Observations:</strong> 541,909 transactional rows from <code>Online Retail.xlsx</code>.</li>
      <li><strong>Guest Checkout Removal:</strong> 135,080 records lacking <code>CustomerID</code> were pruned.</li>
      <li><strong>Cancellation Filtering:</strong> 8,905 cancelled orders (prefixed with 'C') or non-positive quantities and prices were filtered.</li>
      <li><strong>Customer 360 Synthesis:</strong> Exactly <strong>397,884 clean purchase items</strong> were grouped into <strong>4,338 rich Customer 360 documents</strong>.</li>
    </ul>

    <h2 class="section-heading">3. MongoDB Document Schema & Index Governance</h2>
    <p>All customer profiles are stored in the <code>customers</code> collection under MongoDB Atlas. Data integrity is enforced using <code>$jsonSchema</code> validation.</p>

    <div class="figure-container">
      <img src="{schema_b64}" alt="MongoDB Customer 360 Database Schema">
      <div class="figure-caption">Figure 1: Hierarchical Customer 360 Document Schema and Index Architecture</div>
    </div>

    <h3 class="sub-heading">Secondary B-Tree Index Optimization Strategy</h3>
    <table class="data-table">
      <thead>
        <tr>
          <th>Index Specification</th>
          <th>Type</th>
          <th>Query Pattern / Engine Optimization</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>{{ customer_id: 1 }}</code></td>
          <td>Unique B-Tree</td>
          <td>Guarantees deduplication and enables O(1) point lookups for dashboard searches (IXSCAN).</td>
        </tr>
        <tr>
          <td><code>{{ country: 1 }}</code></td>
          <td>B-Tree</td>
          <td>Accelerates regional market filtering and geographic revenue aggregation ($group stage).</td>
        </tr>
        <tr>
          <td><code>{{ last_purchase_date: 1 }}</code></td>
          <td>B-Tree</td>
          <td>Enables fast range scans for Recency calculations and 90-day churn segmentation.</td>
        </tr>
        <tr>
          <td><code>{{ first_purchase_date: 1 }}</code></td>
          <td>B-Tree</td>
          <td>Optimizes triangular monthly cohort acquisition grouping and tenure extraction.</td>
        </tr>
        <tr>
          <td><code>{{ total_orders_count: 1 }}</code></td>
          <td>B-Tree</td>
          <td>Fast filtering for VIP repeat-buyer cohorts and loyalty tier queries.</td>
        </tr>
      </tbody>
    </table>

    <h2 class="section-heading">4. In-Database MongoDB Aggregation Pipelines</h2>
    <p>Rather than pulling high-volume JSON documents into application memory, feature extraction is executed directly in MongoDB's C++ aggregation engine.</p>

    <h3 class="sub-heading">RFM & Churn Labeling Pipeline</h3>
    <pre class="code-block">db.customers.aggregate([
  {{
    $project: {{
      customer_id: 1, country: 1,
      frequency: {{ $size: {{ $ifNull: ["$orders", []] }} }},
      monetary: {{ $round: [{{ $sum: "$orders.order_total" }}, 2] }},
      total_items: {{ $sum: "$orders.items_count" }},
      recency_days: {{
        $round: [{{ $divide: [{{ $subtract: [ISODate("2011-12-10T00:00:00Z"), "$last_purchase_date"] }}, 86400000] }}, 1]
      }}
    }}
  }},
  {{
    $project: {{
      customer_id: 1, country: 1, recency_days: 1, frequency: 1, monetary: 1,
      avg_order_value: {{ $round: [{{ $cond: [{{ $gt: ["$frequency", 0] }}, {{ $divide: ["$monetary", "$frequency"] }}, 0] }}, 2] }},
      is_churned: {{ $cond: [{{ $gte: ["$recency_days", 90] }}, 1, 0] }}
    }}
  }}
]);</pre>

    <h2 class="section-heading">5. Machine Learning & Predictive Modeling</h2>

    <h3 class="sub-heading">5.1 Unsupervised RFM Segmentation (K-Means)</h3>
    <p>Because transaction frequency and spend are log-normally distributed, features were transformed via <code>ln(1 + x)</code> and scaled. An optimal <strong>k = 4</strong> was determined, yielding a <strong>Silhouette Score of 0.337</strong>.</p>

    <table class="data-table">
      <thead>
        <tr>
          <th>Cluster</th>
          <th>Mean Recency</th>
          <th>Mean Frequency</th>
          <th>Mean Spend (£)</th>
          <th>Assigned Customer Persona</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Cluster 0</strong></td>
          <td>180.4 days</td>
          <td>1.3 orders</td>
          <td>£341.30</td>
          <td>Dormant / One-Time Buyers</td>
        </tr>
        <tr>
          <td><strong>Cluster 1</strong></td>
          <td>11.5 days</td>
          <td>13.8 orders</td>
          <td>£8,133.60</td>
          <td>VIP Champions & Super-Users</td>
        </tr>
        <tr>
          <td><strong>Cluster 2</strong></td>
          <td>17.2 days</td>
          <td>2.2 orders</td>
          <td>£560.20</td>
          <td>Active Regular Shoppers</td>
        </tr>
        <tr>
          <td><strong>Cluster 3</strong></td>
          <td>70.9 days</td>
          <td>4.1 orders</td>
          <td>£1,811.50</td>
          <td>Mid-Tier Maturing Accounts</td>
        </tr>
      </tbody>
    </table>

    <h3 class="sub-heading">5.2 Supervised XGBoost Churn Classifier</h3>
    <p>To eliminate data leakage, <code>recency_days</code> was strictly excluded from training features. An XGBoost Classifier was trained with <code>scale_pos_weight = 1.99</code> to handle class balance.</p>

    <table class="data-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Score</th>
          <th>Interpretation</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>ROC-AUC</strong></td>
          <td><strong>0.9558</strong></td>
          <td>Exceptional discriminative capability between active and churning customers.</td>
        </tr>
        <tr>
          <td><strong>PR-AUC</strong></td>
          <td><strong>0.9292</strong></td>
          <td>High precision maintained across imbalanced minority churn class.</td>
        </tr>
        <tr>
          <td><strong>Accuracy</strong></td>
          <td><strong>87.00%</strong></td>
          <td>High overall classification accuracy on holdout test set (n = 1,085).</td>
        </tr>
        <tr>
          <td><strong>F1-Score</strong></td>
          <td><strong>0.8190</strong></td>
          <td>Balanced precision (76.5%) and recall (88.1%).</td>
        </tr>
      </tbody>
    </table>

    <div class="figure-container">
      <img src="{arch_b64}" alt="End-to-End System Architecture">
      <div class="figure-caption">Figure 2: End-to-End Architecture: Ingestion, MongoDB Storage, Aggregations, ML & Streamlit UI</div>
    </div>

    <h2 class="section-heading">6. Interactive Streamlit Presentation Tier</h2>
    <p>A clean, light-themed web interface (<code>app/dashboard.py</code>) provides interactive access to the intelligence layer:</p>
    <ul>
      <li><strong>Overview & Executive KPIs:</strong> Real-time KPI scorecards (£8.91M revenue, 4,338 customers, 33.4% churn) and regional sales distributions.</li>
      <li><strong>Persona Segmentation:</strong> RFM quartile breakdown and interactive 2D log-scaled scatter plots.</li>
      <li><strong>Cohort Retention Matrix:</strong> Triangular monthly cohort retention heatmap tracking retention decay across 12 months.</li>
      <li><strong>Customer 360 Risk Scoring:</strong> Instant point query for any Customer ID with an animated radial churn risk gauge.</li>
    </ul>

    <h2 class="section-heading">7. System Replication & Execution</h2>
    <p>The project can be executed directly using the included batch launcher or command line:</p>
    <pre class="code-block"># Option 1: Double-click Windows batch launcher
run_dashboard.bat

# Option 2: Run via terminal
cd d:\\MongoDB
.\\.venv\\Scripts\\streamlit.exe run app/dashboard.py</pre>
  </div>

</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Generated HTML Report: {OUTPUT_HTML} ({OUTPUT_HTML.stat().st_size:,} bytes)")


if __name__ == "__main__":
    print("[INFO] Compiling Project Reports in Document Format...")
    generate_docx()
    generate_html()
    print("[SUCCESS] All document reports compiled successfully!")
