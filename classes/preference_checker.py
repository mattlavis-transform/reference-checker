import json
import os
from docx import Document
import classes.globals as g
from classes.preference import Preference
from classes.database import Database


class PreferenceChecker(object):
    """
    Part A: First-Come First-Served Quotas
    Part B: First-Come First-Served Quotas
    Part C: Licence Managed Quotas
    
    Delete the rows that just say "section"
    """

    def __init__(self, origin):
        self.origin = origin
        self.get_config()
        print("Checking preferences for", self.origin)
        # self.start_log()
        self.get_preference_data_from_db()
        self.get_preferences_from_word_document()
        self.compare_quotas()

    def get_config(self):
        with open(g.app.preferences_config) as jsonFile:
            jsonObject = json.load(jsonFile)
            obj = jsonObject[self.origin]
            self.country = obj["country"]
            self.source = os.path.join(g.app.preferences_source, obj["source"])
            self.dest = os.path.join(g.app.preferences_dest, self.origin + ".txt")
            a = 1

    def start_log(self):
        f = open(g.app.quotas_log, "w+")
        f.close()

    def get_preference_data_from_db(self):
        d = Database()
        sql = """select m.measure_sid, m.goods_nomenclature_item_id,
        m.geographical_area_id, m.ordernumber as quota_order_number_id,
        string_agg(
            case when mc.monetary_unit_code is null then trim(to_char(mc.duty_amount, '90.00')) || '%'
            else '£' || trim(to_char(mc.duty_amount, '99990.00')) || ' / ' || mc.measurement_unit_code
            end, 
            case when mc.duty_expression_id in ('17', '35') then ' MAX '
            when mc.duty_expression_id in ('15') then ' MIN '
            else ' + ' end order by mc.duty_expression_id) as duty
        from utils.materialized_measures_real_end_dates m, measure_components mc
        where m.measure_sid = mc.measure_sid 
        and m.measure_type_id in ('142', '145')
        and m.geographical_area_id = '""" + self.origin + """'
        and (m.validity_end_date is null or m.validity_end_date >= '2022-01-01')
        group by m.measure_sid, m.goods_nomenclature_item_id, m.geographical_area_id, m.ordernumber
        order by m.goods_nomenclature_item_id, m.measure_sid;"""

        g.app.duties_dict = {}

        rows = d.run_query(sql.replace("\n", ""))
        for row in rows:
            measure_sid = row[0]
            goods_nomenclature_item_id = row[1]
            geographical_area_id = row[2]
            quota_order_number_id = row[3]
            duty = row[4]
            item = {
                    "goods_nomenclature_item_id": goods_nomenclature_item_id,
                    "duty": duty,
                    "geographical_area_id": geographical_area_id,
                    "quota_order_number_id": quota_order_number_id,
                    "measure_sid": measure_sid
                }
            if goods_nomenclature_item_id not in g.app.duties_dict:
                g.app.duties_dict[goods_nomenclature_item_id] = []

            g.app.duties_dict[goods_nomenclature_item_id].append(item)
            
        a = 1

    def get_preferences_from_word_document(self):
        self.preferences = []
        index = 0
        document = Document(self.source)
        table = document.tables[0]
        for row in table.rows:
            if "Commodity code" not in row.cells[0].text:
                index += 1
                if len(row.cells) == 4:
                    preference = Preference()
                    preference.goods_nomenclature_item_id = row.cells[0].text.strip()
                    preference.duty = row.cells[1].text.strip()
                    preference.staging = row.cells[2].text.strip()
                    preference.notes = row.cells[3].text.strip()
                    # preference.cleanse()
                    self.preferences.append(preference)

                elif len(row.cells) == 2:
                    preference = Preference()
                    preference.goods_nomenclature_item_id = row.cells[0].text.strip()
                    preference.duty = row.cells[1].text.strip()
                    # preference.cleanse()
                    self.preferences.append(preference)
                    
                print(str(index))

    def compare_quotas(self):
        for preference in self.preferences:
            try:
                ret = g.app.duties_dict[preference.goods_nomenclature_item_id]
            except:
                a = 1
                pass