import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO

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

    # Use 'Shipment Number' field if available; otherwise default to 1
    shipment_match = re.search(r"Shipment Number:\s*(\d+)", text)
    qty = int(shipment_match.group(1)) if shipment_match else 1

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "qty": qty,
    }

def make_label_pdf(bol, so, scac, qty):
    pdfs = []
    for i in range(1, qty + 1):
        pdf = FPDF(unit='pt', format=(792, 612))  # 11x8.5 landscape
        pdf.add_page()
        pdf.set_auto_page_break(False)
        pdf.set_font("Arial", 'B', 100)  # increase font size

        # Draw content vertically stretched across the page
        vertical_positions = [80, 230, 380]
        pdf.set_y(vertical_positions[0])
        pdf.cell(792, 100, so, ln=1, align='C')
        pdf.set_y(vertical_positions[1])
        pdf.cell(792, 100, scac, ln=1, align='C')
        pdf.set_y(vertical_positions[2])
        pdf.cell(792, 100, f"{i} of {qty}", ln=1, align='C')

        buffer = BytesIO()
        buffer.write(pdf.output(dest='S').encode('latin1'))
        buffer.seek(0)
        pdfs.append((f"{bol}_{i}_of_{qty}.pdf", buffer.read()))
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
                label_pdfs = make_label_pdf(fields["bol"], fields["so"], fields["scac"], fields["qty"])
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
