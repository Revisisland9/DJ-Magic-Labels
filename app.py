import streamlit as st
import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO

st.set_page_config(page_title="BOL Label Generator", 
layout="centered")
st.title("📦 Shipping Label Generator")

uploaded_files = st.file_uploader(
    "Upload BOL PDFs (single combined or multiple individual)",
    type="pdf",
    accept_multiple_files=True


# --- Utility Functions ---
def extract_fields(text):
    bol_match = re.search(r"BOL Number:\s*(PLS\d+)", text)
    scac_match = re.search(r"SCAC:\s*(\w+)", text)
    so_match = re.search(r"Sales Order:\s*(SO-\d+[\w-]*)", text)
    qty_match = re.search(r"(\d+)\s+\d{3,}\s+GRAND TOTAL", text)

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "qty": int(qty_match.group(1)) if qty_match else 1,
    }

def make_label_pdf(bol, so, scac, qty):
    pdfs = []
    for i in range(1, qty + 1):
        pdf = FPDF(orientation='L', unit='in', format=(11, 8.5))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 72)

        pdf.set_y(1.0)
        pdf.cell(11, 2, f"SALES ORDER: {so}", ln=1, align='C')
        pdf.cell(11, 2, f"SCAC: {scac}", ln=1, align='C')
        pdf.cell(11, 2, f"PIECE {i} of {qty}", ln=1, align='C')

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        pdfs.append((f"{bol}_{i}_of_{qty}.pdf", buffer.read()))
    return pdfs

# --- Main Processing ---
if uploaded_files:
    all_labels = []

    for uploaded_file in uploaded_files:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for page in doc:
            text = page.get_text()
            fields = extract_fields(text)
            if fields["bol"]:
                label_pdfs = make_label_pdf(fields["bol"], 
fields["so"], fields["scac"], fields["qty"])
                all_labels.extend(label_pdfs)

    if all_labels:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, data in all_labels:
                zipf.writestr(filename, data)
        zip_buffer.seek(0)

        st.success(f"Generated {len(all_labels)} labels from 
{len(uploaded_files)} file(s).")
        st.download_button(
            label="📥 Download ZIP of Labels",
            data=zip_buffer,
            file_name="shipping_labels.zip",
            mime="application/zip"
        )
    else:
        st.warning("No valid BOLs found in the uploaded file(s).")
import 
streamlit as st import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO

st.set_page_config(page_title="BOL Label Generator", 
layout="centered")
st.title("📦 Shipping Label Generator")

uploaded_files = st.file_uploader("Upload BOL PDFs (single combined 
or multiple individual)", type="pdf", accept_multiple_files=True)

# --- Utility Functions ---
def extract_fields(text):
    bol_match = re.search(r"BOL Number:\s*(PLS\d+)", text)
    scac_match = re.search(r"SCAC:\s*(\w+)", text)
    so_match = re.search(r"Sales Order:\s*(SO-\d+[\w-]*)", text)
    qty_match = re.search(r"(\d+)\s+\d{3,}\s+GRAND TOTAL", text)

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "qty": int(qty_match.group(1)) if qty_match else 1,
    }

def make_label_pdf(bol, so, scac, qty):
    pdfs = []
    for i in range(1, qty + 1):
        pdf = FPDF(orientation='L', unit='in', format=(11, 8.5))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 72)

        pdf.set_y(1.0)
        pdf.cell(11, 2, f"SALES ORDER: {so}", ln=1, align='C')
        pdf.cell(11, 2, f"SCAC: {scac}", ln=1, align='C')
        pdf.cell(11, 2, f"PIECE {i} of {qty}", ln=1, align='C')

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        pdfs.append((f"{bol}_{i}_of_{qty}.pdf", buffer.read()))
    return pdfs

# --- Main Processing ---
if uploaded_files:
    all_labels = []

    for uploaded_file in uploaded_files:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for page in doc:
            text = page.get_text()
            fields = extract_fields(text)
            if fields["bol"]:
                label_pdfs = make_label_pdf(fields["bol"], 
fields["so"], fields["scac"], fields["qty"])
                all_labels.extend(label_pdfs)

    if all_labels:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, data in all_labels:
                zipf.writestr(filename, data)
        zip_buffer.seek(0)

        st.success(f"Generated {len(all_labels)} labels from 
{len(uploaded_files)} file(s).")
        st.download_button(
            label="📥 Download ZIP of Labels",
            data=zip_buffer,
            file_name="shipping_labels.zip",
            mime="application/zip"
        )
    else:
        st.warning("No valid BOLs found in the uploaded file(s).")
import 
streamlit as st import fitz  # PyMuPDF
import re
from fpdf import FPDF
import zipfile
from io import BytesIO

st.set_page_config(page_title="BOL Label Generator", layout="centered")
st.title("📦 Shipping Label Generator")

uploaded_files = st.file_uploader("Upload BOL PDFs (single combined or 
multiple individual)", type="pdf", accept_multiple_files=True)

# --- Utility Functions ---
def extract_fields(text):
    bol_match = re.search(r"BOL Number:\s*(PLS\d+)", text)
    scac_match = re.search(r"SCAC:\s*(\w+)", text)
    so_match = re.search(r"Sales Order:\s*(SO-\d+[\w-]*)", text)
    qty_match = re.search(r"(\d+)\s+\d{3,}\s+GRAND TOTAL", text)

    return {
        "bol": bol_match.group(1) if bol_match else "",
        "scac": scac_match.group(1) if scac_match else "",
        "so": so_match.group(1) if so_match else "",
        "qty": int(qty_match.group(1)) if qty_match else 1,
    }

def make_label_pdf(bol, so, scac, qty):
    pdfs = []
    for i in range(1, qty + 1):
        pdf = FPDF(orientation='L', unit='in', format=(11, 8.5))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 72)

        pdf.set_y(1.0)
        pdf.cell(11, 2, f"SALES ORDER: {so}", ln=1, align='C')
        pdf.cell(11, 2, f"SCAC: {scac}", ln=1, align='C')
        pdf.cell(11, 2, f"PIECE {i} of {qty}", ln=1, align='C')

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        pdfs.append((f"{bol}_{i}_of_{qty}.pdf", buffer.read()))
    return pdfs

# --- Main Processing ---
if uploaded_files:
    all_labels = []

    for uploaded_file in uploaded_files:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for page in doc:
            text = page.get_text()
            fields = extract_fields(text)
            if fields["bol"]:
                label_pdfs = make_label_pdf(fields["bol"], fields["so"], 
fields["scac"], fields["qty"])
                all_labels.extend(label_pdfs)

    if all_labels:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, data in all_labels:
                zipf.writestr(filename, data)
        zip_buffer.seek(0)

        st.success(f"Generated {len(all_labels)} labels from 
{len(uploaded_files)} file(s).")
        st.download_button(
            label="📥 Download ZIP of Labels",
            data=zip_buffer,
            file_name="shipping_labels.zip",
            mime="application/zip"
        )
    else:
        st.warning("No valid BOLs found in the uploaded file(s).")

