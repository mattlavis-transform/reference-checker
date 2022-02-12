import sys
from docx import Document
import classes.globals as g
from classes.quota import Quota
from classes.database import Database


class QuotaChecker(object):
    """
    Part A: First-Come First-Served Quotas
    Part B: First-Come First-Served Quotas
    Part C: Licence Managed Quotas
    
    Delete the rows that just say "section"
    """

    def __init__(self):
        self.quotas = []
        print("Checking quotas")
        self.start_log()
        self.get_quota_data_from_db()
        self.get_quotas_from_word_document()
        self.validate_quotas()
        
    def start_log(self):
        f = open(g.app.quotas_log, "w+")
        f.close()
        
    def get_quota_data_from_db(self):
        self.get_quota_commodities_from_db()
        self.get_quota_origins_from_db()
        self.get_quota_definitions_from_db()
        self.get_duties_from_db()
        
    def get_quota_commodities_from_db(self):
        d = Database()
        sql = """
        select distinct ordernumber, goods_nomenclature_item_id, validity_start_date, measure_sid
        from utils.materialized_measures_real_end_dates m
        where (validity_end_date is null or validity_end_date >= '2022-01-01')
        and ordernumber is not null
        order by 1, 2;
        """

        g.app.quota_commodities = []
        g.app.quota_commodities_dict = {}
        rows = d.run_query(sql)
        for row in rows:
            quota_order_number_id = row[0]
            goods_nomenclature_item_id = row[1]
            validity_start_date = row[2]
            measure_sid = row[3]
            item = {
                    "goods_nomenclature_item_id": goods_nomenclature_item_id,
                    "validity_start_date": validity_start_date,
                    "measure_sid": measure_sid,
                    "quota_order_number_id": quota_order_number_id
                }
            g.app.quota_commodities.append(item)
            if quota_order_number_id not in g.app.quota_commodities_dict:
                g.app.quota_commodities_dict[quota_order_number_id] = []

            g.app.quota_commodities_dict[quota_order_number_id].append(item)

    def get_quota_origins_from_db(self):
        d = Database()
        sql = """
        with cte_geo as (
            select distinct on (gad.geographical_area_id) gad.geographical_area_id, gad.description 
            from geographical_area_descriptions gad, geographical_area_description_periods gadp 
            where gad.geographical_area_sid = gadp.geographical_area_sid 
            order by gad.geographical_area_id, gadp.validity_start_date  desc
        )
        select qon.quota_order_number_id, qono.geographical_area_id, cte_geo.description 
        from quota_order_number_origins qono, quota_order_numbers qon, cte_geo
        where qono.quota_order_number_sid = qon.quota_order_number_sid 
        and qono.validity_start_date <= '2022-12-31'
        and (qono.validity_end_date is null or qono.validity_end_date >= '2022-01-01')
        and cte_geo.geographical_area_id = qono.geographical_area_id 

        union 

        select distinct m.ordernumber as quota_order_number_id, m.geographical_area_id, cte_geo.description 
        from utils.materialized_measures_real_end_dates m, cte_geo
        where (validity_end_date is null or validity_end_date >= '2022-01-01')
        and cte_geo.geographical_area_id = m.geographical_area_id 
        and ordernumber like '054%'
        order by 1, 2;
        """

        g.app.quota_origins_dict = {}
        rows = d.run_query(sql)
        for row in rows:
            quota_order_number_id = row[0]
            geographical_area_id = row[1]
            geographical_area_description = row[2]
            item = {
                    "geographical_area_description": geographical_area_description,
                    "geographical_area_id": geographical_area_id,
                    "quota_order_number_id": quota_order_number_id
                }
            if quota_order_number_id not in g.app.quota_origins_dict:
                g.app.quota_origins_dict[quota_order_number_id] = []

            g.app.quota_origins_dict[quota_order_number_id].append(item)

    def get_quota_definitions_from_db(self):
        d = Database()
        sql = """
        select quota_order_number_id, validity_start_date, validity_end_date, initial_volume 
        from quota_definitions qd 
        where qd.validity_start_date <= '2022-12-31'
        and qd.validity_end_date >= '2022-01-01'
        order by qd.quota_order_number_id
        """

        g.app.quota_definitions_dict = {}
        rows = d.run_query(sql)
        for row in rows:
            quota_order_number_id = row[0]
            validity_start_date = row[1]
            validity_end_date = row[2]
            initial_volume = row[3]
            try:
                initial_volume = int(initial_volume)
            except:
                initial_volume = 0
            item = {
                    "quota_order_number_id": quota_order_number_id,
                    "validity_start_date": validity_start_date,
                    "validity_end_date": validity_end_date,
                    "initial_volume": initial_volume
                }
            if quota_order_number_id not in g.app.quota_definitions_dict:
                g.app.quota_definitions_dict[quota_order_number_id] = []

            g.app.quota_definitions_dict[quota_order_number_id].append(item)

    def get_duties_from_db(self):
        d = Database()
        sql = """
        select m.measure_sid, m.goods_nomenclature_item_id,
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
        and m.ordernumber is not null
        and (m.validity_end_date is null or m.validity_end_date >= '2022-01-01')
        group by m.measure_sid, m.goods_nomenclature_item_id, m.geographical_area_id, m.ordernumber
        order by m.measure_sid 
        """

        g.app.quota_duties_dict = {}
        rows = d.run_query(sql)
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
            if quota_order_number_id not in g.app.quota_duties_dict:
                g.app.quota_duties_dict[quota_order_number_id] = []

            g.app.quota_duties_dict[quota_order_number_id].append(item)

    def get_quotas_from_word_document(self):
        document = Document(g.app.quotas_source)
        index = 0
        done = False
        for table in document.tables:
            if not done:
                for row in table.rows:
                    index += 1
                    if len(row.cells) == 8:
                        quota = Quota()
                        quota.quota_order_number_id = row.cells[0].text.strip()
                        quota.commodity_string = row.cells[1].text.strip()
                        quota.origin = row.cells[2].text.strip()
                        if quota.origin == "":
                            a = 1
                        quota.quota_duty_rate_string = row.cells[3].text.strip()
                        quota.quota_volume = row.cells[4].text.strip()
                        quota.quota_open_date = row.cells[5].text.strip()
                        quota.quota_close_date = row.cells[6].text.strip()
                        quota.quota_volume_2021 = row.cells[7].text.strip()
                        quota.check_validity()
                        
                        if quota.valid:
                            print ("Getting quota", quota.quota_order_number_id)
                            quota.cleanse()
                            quota.get_commodities()
                            quota.get_duties()
                            self.quotas.append(quota)

                    if index > 200000:
                        done = True

    def validate_quotas(self):
        for quota in self.quotas:
            quota.validate()
