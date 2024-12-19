from PySide6.QtWidgets import QApplication, QFileDialog
from docx.shared import Inches
from docx import Document
import sys, os


def inwestigation_docx(docx_path, output_path, data):
    
    doc = Document(docx_path)
    xml_content = doc._element
    namespaces = doc.element.nsmap

    for paragraph in doc.paragraphs:  # Replace text in paragraphs (Check all runs)
        for key, value in data.items():
            if key in paragraph.text:
                #print(f"Found '{key}' in paragraph: {paragraph.text}")  # Debugging
                for run in paragraph.runs:
                    #print(run.text)
                    if key in run.text or key.lower() in run.text.lower():
                        #print(f"Replacing '{key}' with '{value}' in run: {run.text}")  # Debugging
                        run.text = run.text.replace(key, value)

    for section in doc.sections:  # Replace text in headers and footers (Check all paragraphs in sections)
        header = section.header
        footer = section.footer
        for paragraph in header.paragraphs + footer.paragraphs:
            for key, value in data.items():
                if key in paragraph.text:
                    #print(f"Found '{key}' in header/footer paragraph: {paragraph.text}")  # Debugging
                    for run in paragraph.runs:
                        if key in run.text:
                            #print(f"Replacing '{key}' with '{value}' in run: {run.text}")  # Debugging
                            run.text = run.text.replace(key, value)

    for shape in xml_content.xpath("//w:txbxContent"):  # Replace text in shapes (textboxes) using XML
        for node in shape.xpath(".//w:t", namespaces=namespaces):

            if node.text:
                for key, value in data.items():
                    if key in node.text:
                        node.text = node.text.replace(key, value)

    doc.save(output_path)

def select_folder_and_process(path_to_doc=None, output_folder=None, data=None):

    if data is None:
        data = {}

    if not path_to_doc:
        path_to_doc = QFileDialog.getExistingDirectory(None, "Select Folder with DOCX Files")  # Select input folder
    if not path_to_doc:
        return

    output_folder = QFileDialog.getExistingDirectory(None, "Select Output Folder", os.path.expanduser("~/Desktop"))  # Select output folder
    if not output_folder:
        return

    for filename in os.listdir(path_to_doc):  # Process all files in the selected folder
        if filename.endswith('.docx'):
            docx_path = os.path.join(path_to_doc, filename)
            output_path = os.path.join(output_folder, f"modified_{filename}")
            inwestigation_docx(docx_path, output_path, data)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    data = {'[NR_DZIALKI]': '',
            '[IDENTYFIKATOR]': '',
            '[WOJ]': '',
            '[POW]': '',
            '[JEWID]': '',
            '[JEWID_ID]': '',
            '[OBR]': '',
            '[OBR_ID]': '',
            '[ARKUSZ]': '',
            '[DATA_OKLADKA]': '',
            '[DATA_SPIS]': '',
            '[DATA_SPR]': '',
            '[DATA]': '',
            '[CEL]': '',
            '[WYKONAWCA]': '',
            '[KIEROWNIK]': '',
            '[KIEROWNIK_UPR]': '',
            '[UPRAC]': '',
            '[TERMIN_R]': '',
            '[TERMIN_Z]': ''
            }














