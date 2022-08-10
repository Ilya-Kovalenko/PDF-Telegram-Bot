from PyPDF2 import PdfWriter, PdfReader, PdfMerger
import os
from docx2pdf import convert
import pythoncom


def delete(filename: str) -> None:
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    os.remove(path)


def merge(pdf_list: list) -> str:
    merger = PdfMerger()

    for pdf in pdf_list:
        merger.append(f"PDF Input/{pdf}")

    merger.write(f"PDF Output/merged-{pdf_list[0]}")
    merger.close()

    return f"PDF Output/merged-{pdf_list[0]}"


def split(pdf: str) -> list:
    reader = PdfReader(f"PDF Input/{pdf}")

    file_names = []

    for i in range(reader.getNumPages()):
        writer = PdfWriter()
        current_page = reader.getPage(i)
        writer.addPage(current_page)

        output_filename = f"PDF Output/split-page-{i + 1}-{pdf}"
        file_names.append(output_filename)
        with open(output_filename, "wb") as out:
            writer.write(out)

    return file_names


def docx_convert(docx_file: str) -> str:
    pythoncom.CoInitialize()
    convert(f"PDF Input/{docx_file}", f"PDF Output/converted-{docx_file[:-5]}.pdf")

    return f"PDF Output/converted-{docx_file[:-5]}.pdf"


