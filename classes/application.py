import os
import json
from dotenv import load_dotenv
import xlsxwriter
from docx import Document
from docx.shared import Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.shared import OxmlElement, qn
from classes.quota_checker import QuotaChecker
from classes.preference_checker import PreferenceChecker
from classes.classification_checker import ClassificationChecker
from classes.pharma_checker import PharmaChecker


class Application(object):
    def __init__(self):
        load_dotenv('.env')
        
        self.resources_folder = os.path.join(os.getcwd(), "resources")
        
        # Quota-related
        self.quotas_source = os.path.join(self.resources_folder, "quotas", "Customs_Tariff_Quota_Reference_Document__V2.2.docx")
        self.quotas_log = os.path.join(self.resources_folder, "quotas", "quotas_errors.log")
        
        # Preference-related
        self.preferences_source = os.path.join(self.resources_folder, "preferences", "source")
        self.preferences_dest = os.path.join(self.resources_folder, "preferences", "dest")
        self.preferences_config = os.path.join(self.resources_folder, "preferences", "config", "preferences_config.json")
        self.preferences_log = os.path.join(self.resources_folder, "preferences", "log", "preferences_{{preference}}_errors.log")

        # Classification-related
        self.classification_source_filename = os.getenv('CLASSIFICATION_SOURCE_FILENAME')
        # self.classification_source = os.path.join(self.resources_folder, "classification", "211202-JWR-TRD 10 digit working master 17 Jan.docx")
        self.classification_source = os.path.join(self.resources_folder, "classification", self.classification_source_filename)
        self.classification_log = os.path.join(self.resources_folder, "classification", "classification_errors.log")
        self.differences_folder = os.path.join(self.resources_folder, "classification", "differences")

        # Pharma-related
        # self.pharma_source = os.path.join(self.resources_folder, "pharma", "pharma table 10.xlsx")
        # self.pharma_source = os.path.join(self.resources_folder, "pharma", "pharma table 12.xlsx")
        self.pharma_source = os.path.join(self.resources_folder, "pharma", "pharma table 13.xlsx")
        if "10" in self.pharma_source:
            log_file =  "pharma_errors_10.log"
        elif "12" in self.pharma_source:
            log_file =  "pharma_errors_12.log"
        elif "13" in self.pharma_source:
            log_file =  "pharma_errors_13.log"
        
        self.pharma_log = os.path.join(self.resources_folder, "pharma", log_file)
        
    def check_quotas(self):
        quota_checker = QuotaChecker()

    def check_preferences(self, origin):
        preference_checker = PreferenceChecker(origin)
        
    def check_classification(self, do_from, do_to):
        classification_checker = ClassificationChecker(do_from, do_to)

    def check_pharma(self):
        pharma = PharmaChecker()

    def write_classification_report(self):
        results = []
        for f in os.listdir(self.differences_folder):
            if f.endswith('.json'):
                results.append(f)
        results = sorted(results)
        
        # Create an Excel document
        filename_xlsx = os.path.join(self.differences_folder, "differences.xlsx")
        workbook = xlsxwriter.Workbook(filename_xlsx)

        format_left = workbook.add_format({'align': 'left', 'valign': 'top', 'text_wrap': 'true'})
        format_centre = workbook.add_format({'align': 'center', 'valign': 'top', 'text_wrap': 'true'})
        format_right = workbook.add_format({'align': 'right', 'valign': 'top', 'text_wrap': 'true'})
        format_bold = workbook.add_format({'bold': 'true', 'valign': 'top', 'text_wrap': 'true'})
        format_centre_bold = workbook.add_format({'bold': 'true', 'align': 'center', 'valign': 'top', 'text_wrap': 'true'})

        worksheet_overview = workbook.add_worksheet("differences")
        worksheet_overview.freeze_panes(1, 0)
        worksheet_overview.set_column(0, 5, 15)
        worksheet_overview.set_column(3, 3, 70)
        worksheet_overview.set_column(6, 6, 70)
        
        worksheet_overview.write('A1', "Chapter" , format_bold)

        worksheet_overview.write('B1', "Document commodity" , format_bold)
        worksheet_overview.write('C1', "Document indent" , format_centre_bold)
        worksheet_overview.write('D1', "Document description" , format_bold)

        worksheet_overview.write('E1', "Database commodity" , format_bold)
        worksheet_overview.write('F1', "Database indent" , format_centre_bold)
        worksheet_overview.write('G1', "Database description" , format_bold)

        row_count = 1

        for result in results:
            filename = os.path.join(self.differences_folder, result)
            chapter_id = result.replace(".json", "")
            chapter_id = chapter_id.replace("differences_", "")
            print(chapter_id)
            with open(filename) as jsonFile:
                jsonObject = json.load(jsonFile)
                for item in jsonObject:
                    item1 = ""
                    item2 = ""
                    if item["db"]:
                        if item["db"]["goods_nomenclature_item_id"]:
                            if item["db"]["goods_nomenclature_item_id"] == "0303541096":
                                a = 1
                    try:
                        item1 = item["document"]["goods_nomenclature_item_id"]
                    except:
                        pass
                    try:
                        item2 = item["db"]["goods_nomenclature_item_id"]
                    except:
                        pass

                    if item1 != "" or item2 != "":
                        row_count += 1
                        worksheet_overview.write('A' + str(row_count), chapter_id, format_left)
                        if item["document"]:
                            if item["document"]["goods_nomenclature_item_id"]:
                                worksheet_overview.write('B' + str(row_count), item["document"]["goods_nomenclature_item_id"], format_left)
                                worksheet_overview.write('C' + str(row_count), item["document"]["number_indents"], format_centre)
                                worksheet_overview.write('D' + str(row_count), item["document"]["description"], format_left)

                        if item["db"]:
                            if item["db"]["goods_nomenclature_item_id"]:
                                worksheet_overview.write('E' + str(row_count), item["db"]["goods_nomenclature_item_id"], format_left)
                                worksheet_overview.write('F' + str(row_count), item["db"]["number_indents"], format_centre)
                                worksheet_overview.write('G' + str(row_count), item["db"]["description"], format_left)
                jsonFile.close()

        workbook.close()

    def process_null(self, s):
        if s is None:
            return ""
        else:
            if isinstance(s, list):
                s = ", ".join(s)

            return s.strip()

    def set_repeat_table_header(self, row):
        """ set repeat table row on every new page
        """
        tr = row._tr
        trPr = tr.get_or_add_trPr()
        tblHeader = OxmlElement('w:tblHeader')
        tblHeader.set(qn('w:val'), "true")
        trPr.append(tblHeader)
        return row
