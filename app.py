import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import tempfile
import os

st.set_page_config(page_title="BOL Label Generator", layout="centered")
st.title("📦 Shipping Label Generator")

uploaded_files = st.file_uploader(
    "Upload BOL PDFs (single combined or multiple individual)",
    type="pdf",
    accept_multiple_files=True
)

# --- Utility Functions ---
def extract_fields(text):
    bol_match = re.search(r"BOL Number:\s*(PLS\d+)", text)
    scac_match = re.search(r"SCAC:\s*(\w+)", text)
    so_match = re.search(r"Sales Order:\s*(SO-\d+[\w-]*)", text)
    pro_match = re.search(r"Pro Number:\s*(\d+)", text)
    shipment_match = re.search(r"Shipment Number:\s*(\d+)", text)

    qty = int(shipment_match.group(1)) if shipment_match else 1

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "pro": pro_match.group(1) if pro_match else "",
        "qty": qty,
    }

def generate_barcode_image_bytes(pro_number):
    code128 = barcode.get('code128', pro_number, writer=ImageWriter())
    raw_path = os.path.join(tempfile.gettempdir(), pro_number)
    full_path = code128.save(raw_path)  # This returns the full path with .png
    image = Image.open(full_path)
    byte_io = BytesIO()
    image.save(byte_io, format='PNG')
    byte_io.seek(0)
    os.remove(full_path)
    return byte_io

def make_label_pdfs(bol, so, scac, pro, qty):
    pdfs = []
    barcode_stream = generate_barcode_image_bytes(pro)

    for i in range(1, qty + 1):
        # Label A: Pro Number + SCAC + Barcode
        pdf_a = FPDF(unit='pt', format=(792, 612))
        pdf_a.add_page()
        pdf_a.set_auto_page_break(False)
        pdf_a.set_font("Arial", 'B', 72)
        pdf_a.set_y(100)
        pdf_a.cell(792, 100, pro, ln=1, align='C')
        pdf_a.cell(792, 100, scac, ln=1, align='C')
        pdf_a.image(barcode_stream, x=200, y=320, w=400, h=100, name="barcode.png")

        buffer_a = BytesIO()
        buffer_a.write(pdf_a.output(dest='S').encode('latin1'))
        buffer_a.seek(0)
        pdfs.append((f"{bol}_A_{i}_of_{qty}.pdf", buffer_a.read()))

        # Label B: Sales Order + Quantity
        pdf_b = FPDF(unit='pt', format=(792, 612))
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
        pdfs.append((f"{bol}_B_{i}_of_{qty}.pdf", buffer_b.read()))

    return pdfs

# --- Main Processing ---
if uploaded_files:
    all_labels = []
    total_labels = 0
    seen_bols = set()

    for uploaded_file in uploaded_files:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for page in doc:
            text = page.get_text()
            fields = extract_fields(text)
            if fields["bol"] and fields["bol"] not in seen_bols:
                seen_bols.add(fields["bol"])
                st.write("Parsed Fields:", fields)
                label_pdfs = make_label_pdfs(fields["bol"], fields["so"], fields["scac"], fields["pro"], fields["qty"])
                total_labels += len(label_pdfs)
                all_labels.extend(label_pdfs)

    if all_labels:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, data in all_labels:
                zipf.writestr(filename, data)
        zip_buffer.seek(0)

        st.success(f"✅ Generated {total_labels} labels from {len(seen_bols)} unique BOL(s).")
        st.download_button(
            label="📥 Download ZIP of Labels",
            data=zip_buffer,
            file_name="shipping_labels.zip",
            mime="application/zip"
        )
    else:
        st.warning("⚠️ No valid BOLs found in the uploaded file(s).")

