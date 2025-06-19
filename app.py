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
shipper_name = st.text_input("Enter Shipper Name (for signature box on BOL)", value="")

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
        pdf = FPDF(unit='pt', format=(792, 612))  # Landscape
        pdf.add_page()
        pdf.set_auto_page_break(False)

        # Sales Order at the top
        pdf.set_font("Arial", 'B', 80)
        pdf.set_y(60)
        pdf.cell(792, 80, so, ln=1, align='C')

        # Label A portion
        pdf.set_font("Arial", 'B', 72)
        pdf.set_y(160)
        pdf.cell(792, 80, pro if pro else label_id, ln=1, align='C')
        if use_barcode:
            pdf.image(barcode_path, x=196, y=240, w=400, h=100)
        pdf.set_y(360)
        pdf.set_font("Arial", 'B', 100)
        pdf.cell(792, 100, scac, ln=1, align='C')

        # Quantity marker
        pdf.set_y(500)
        pdf.set_font("Arial", 'B', 80)
        pdf.cell(792, 80, f"{i} of {qty}", ln=1, align='C')

        buffer = BytesIO()
        buffer.write(pdf.output(dest='S').encode('latin1'))
        buffer.seek(0)
        pdfs.append(buffer.read())

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
        combined_bol = fitz.open()
        today_str = datetime.now(ZoneInfo("America/Chicago")).strftime("%m/%d/%Y")

        for uploaded_file in uploaded_files:
            file_buffer = BytesIO(uploaded_file.read())
            doc = fitz.open(stream=file_buffer, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                if shipper_name:
                    text_to_insert = f"{shipper_name}    {today_str}"
                    page.insert_text((240, 732), text_to_insert, fontsize=11, fontname="helv", fill=(0, 0, 0))
            combined_bol.insert_pdf(doc)

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

            # Combine label pages into a single PDF
            merged_label_pdf = fitz.open()
            for label_data in all_labels:
                temp_pdf = fitz.open(stream=label_data, filetype="pdf")
                merged_label_pdf.insert_pdf(temp_pdf)

            label_buffer = BytesIO()
            merged_label_pdf.save(label_buffer)
            label_buffer.seek(0)

            bol_buffer = BytesIO()
            combined_bol.save(bol_buffer)
            bol_buffer.seek(0)

            st.success(f"✅ Generated {total_labels} labels from {len(seen_bols)} unique shipment(s).")
            st.download_button(
                label="📅 Download Combined Labels PDF",
                data=label_buffer,
                file_name=f"labels_{timestamp}.pdf",
                mime="application/pdf"
            )
            st.download_button(
                label="📅 Download Combined BOLs PDF",
                data=bol_buffer,
                file_name=f"bols_{timestamp}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ No valid BOLs found in the uploaded file(s).")

