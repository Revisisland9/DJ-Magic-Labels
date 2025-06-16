import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import tempfile
import os
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="R.O.S.S.", layout="centered")
st.title("R.O.S.S. — Rapid Output Shipping System")

manual_mode = st.toggle("Manual Entry", value=False)

# --- Utility Functions ---
def extract_fields(text):
    bol_match = re.search(r"BOL Number:\s*(PLS\d+)", text)
    if not bol_match:
        bol_match = re.search(r"Primary Reference:\s*(PLS\d+)", text)
    if not bol_match:
        bol_match = re.search(r"Load Number:\s*(PLS\d+)", text)

    scac_match = re.search(r"SCAC:\s*(\w+)", text)
    so_match = re.search(r"Sales Order:\s*(SO-\d+[\w-]*)", text)
    pro_match = re.search(r"Pro Number:\s*(\d+)", text)

    qty = 1
    # Updated quantity logic for Normal BOL using "Pieces:"
    pieces_match = re.search(r"(?i)Pieces\s*[:\-]?\s*(\d+)", text)
    if pieces_match:
        qty = int(pieces_match.group(1))

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "pro": pro_match.group(1) if pro_match else "",
        "qty": qty,
    }


def generate_barcode_image_path(pro_number):
    code128 = barcode.get('code128', pro_number, writer=ImageWriter())
    raw_path = os.path.join(tempfile.gettempdir(), f"{pro_number}")
    full_path = code128.save(raw_path, options={"write_text": False})
    return full_path


def make_label_pdfs(label_id, so, scac, pro, qty):
    pdfs = []
    use_barcode = bool(pro)
    barcode_path = generate_barcode_image_path(pro) if use_barcode else None

    for i in range(1, qty + 1):
        # Label A
        pdf_a = FPDF(unit='pt', format=(792, 612))  # Landscape
        pdf_a.add_page()
        pdf_a.set_auto_page_break(False)
        pdf_a.set_font("Arial", 'B', 72)
        pdf_a.set_y(80)
        pdf_a.cell(792, 100, pro if pro else label_id, ln=1, align='C')
        if use_barcode:
            pdf_a.image(barcode_path, x=196, y=200, w=400, h=100)
        pdf_a.set_y(400)
        pdf_a.set_font("Arial", 'B', 100)
        pdf_a.cell(792, 100, scac, ln=1, align='C')

        buffer_a = BytesIO()
        buffer_a.write(pdf_a.output(dest='S').encode('latin1'))
        buffer_a.seek(0)
        pdfs.append((f"{so}_A_{i}_of_{qty}.pdf", buffer_a.read()))

        # Label B
        pdf_b = FPDF(unit='pt', format=(792, 612))  # Landscape
        pdf_b.add_page()
        pdf_b.set_auto_page_break(False)
        pdf_b.set_font("Arial", 'B', 100)
        pdf_b.set_y(100)
        pdf_b.cell(792, 100, so, ln=1, align='C')
        pdf_b.set_y(250)
        pdf_b.cell(792, 100, f"{i} of {qty}", ln=1, align='C')

        buffer_b = BytesIO()
        buffer_b.write(pdf_b.output(dest='S').encode('latin1'))
        buffer_b.seek(0)
        pdfs.append((f"{so}_B_{i}_of_{qty}.pdf", buffer_b.read()))

    if barcode_path and os.path.exists(barcode_path):
        os.remove(barcode_path)

    return pdfs

# --- PDF Mode ---
if not manual_mode:
    uploaded_files = st.file_uploader(
        "Upload BOL PDFs (single combined or multiple individual)",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        all_labels = []
        total_labels = 0
        seen_bols = set()

        for uploaded_file in uploaded_files:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

            for page in doc:
                text = page.get_text()
                fields = extract_fields(text)
                if fields["so"] and fields["so"] not in seen_bols:
                    seen_bols.add(fields["so"])
                    st.write("Parsed Fields:", fields)
                    label_pdfs = make_label_pdfs(
                        fields["so"], fields["so"], fields["scac"], fields["pro"], fields["qty"]
                    )
                    total_labels += len(label_pdfs)
                    all_labels.extend(label_pdfs)

        if all_labels:
            timestamp = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d-%H%M%S")
            zip_filename = f"shipping_labels_{timestamp}.zip"
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for filename, data in all_labels:
                    zipf.writestr(filename, data)
            zip_buffer.seek(0)

            st.success(f"✅ Generated {total_labels} labels from {len(seen_bols)} unique shipment(s).")
            st.download_button(
                label="📥 Download ZIP of Labels",
                data=zip_buffer,
                file_name=zip_filename,
                mime="application/zip"
            )
        else:
            st.warning("⚠️ No valid BOLs found in the uploaded file(s).")

# --- Manual Entry Mode ---
else:
    st.markdown("### Manual Shipment Entry")
    if st.button("🗑️ Clear Form"):
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith("so_") or k.startswith("pro_") or k.startswith("scac_") or k.startswith("qty_")]
        for key in keys_to_clear:
            del st.session_state[key]
        st.success("Form cleared! All manual entries removed.")

    header_cols = st.columns([3, 3, 2, 2])
    header_cols[0].markdown("**Sales Order**")
    header_cols[1].markdown("**Pro Number**")
    header_cols[2].markdown("**SCAC**")
    header_cols[3].markdown("**Quantity**")

    entries = []
    show_next_row = True

    for i in range(20):
        if not show_next_row:
            break
        cols = st.columns([3, 3, 2, 2])
        so = cols[0].text_input("", key=f"so_{i}")
        pro = cols[1].text_input("", key=f"pro_{i}")
        scac = cols[2].text_input("", key=f"scac_{i}")
        qty = cols[3].number_input("", key=f"qty_{i}", min_value=1, value=1, step=1)
        entries.append((so, pro, scac, qty))
        if not so.strip():
            show_next_row = False

    if st.button("🚀 Generate Labels"):
        all_labels = []
        total_labels = 0

        for idx, (so, pro, scac, qty) in enumerate(entries):
            if so.strip():
                label_pdfs = make_label_pdfs(f"MANUAL-{idx+1:03}", so.strip(), scac.strip(), pro.strip(), qty)
                total_labels += len(label_pdfs)
                all_labels.extend(label_pdfs)

        if all_labels:
            timestamp = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y%m%d-%H%M%S")
            zip_filename = f"manual_labels_{timestamp}.zip"
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for filename, data in all_labels:
                    zipf.writestr(filename, data)
            zip_buffer.seek(0)

            st.success(f"✅ Generated {total_labels} labels from manual entries.")
            st.download_button(
                label="📥 Download ZIP of Labels",
                data=zip_buffer,
                file_name=zip_filename,
                mime="application/zip"
            )
        else:
            st.warning("⚠️ No valid manual entries found.")

