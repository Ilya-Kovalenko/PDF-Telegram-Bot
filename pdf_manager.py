from PyPDF2 import PdfWriter, PdfReader, PdfMerger
import os
from docx2pdf import convert
import pythoncom


def delete(filename: str) -> None:
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    os.remove(path)


def merge(pdf_tuple: list) -> str:
    merger = PdfMerger()

    for pdf in pdf_tuple:
        merger.append(pdf)

    merger.write("PDF Output/merged-pdf.pdf")
    merger.close()

    return "PDF Output/merged-pdf.pdf"


def split(pdf: str) -> list:
    reader = PdfReader(pdf)

    file_names = []

    for i in range(reader.getNumPages()):
        writer = PdfWriter()
        current_page = reader.getPage(i)
        writer.addPage(current_page)

        output_filename = f"PDF Output/split-page-{i + 1}.pdf"
        file_names.append(output_filename)
        with open(output_filename, "wb") as out:
            writer.write(out)

    return file_names


def docx_convert(docx_file: str) -> str:
    pythoncom.CoInitialize()
    convert(docx_file, "PDF Output/converted-pdf.pdf")

    return "PDF Output/converted-pdf.pdf"


