from classes.database import Database


class PreferenceError(object):
    def __init__(self, origin, country, reason, scope, commodity_code, measure_type_id, fta_duty_value = None, db_duty_value = None):
        self.origin = origin
        self.country = country
        self.reason = reason
        self.scope = scope
        self.commodity_code = commodity_code
        self.measure_type_id = measure_type_id
        self.fta_duty_value = fta_duty_value
        self.db_duty_value = db_duty_value
        self.descendants = []
        
        self.get_significant_digits()
        
        if "mismatched" not in self.reason.lower():
            self.get_hierarchy()

    def get_significant_digits(self):
        if self.commodity_code[-8:] == "00000000":
            self.entity_type = "chapter"
            self.significant_digits = self.commodity_code[0:2]

        elif self.commodity_code[-6:] == "000000":
            self.entity_type = "heading"
            self.significant_digits = self.commodity_code[0:4]

        elif self.commodity_code[-4:] == "0000":
            self.entity_type = "subheading"
            self.significant_digits = self.commodity_code[0:6]

        elif self.commodity_code[-2:] == "00":
            self.entity_type = "8-digit"
            self.significant_digits = self.commodity_code[0:8]

        else:
            self.entity_type = "commodity"
            self.significant_digits = self.commodity_code

    def get_hierarchy(self):
        d = Database()
        sql = """
        select * from utils."hierarchy" h
        where (select goods_nomenclature_sid
        from utils.hierarchy where productline_suffix = '80'
        and goods_nomenclature_item_id = %s) = any(ancestry_array) and leaf = 1
        union 
        select goods_nomenclature_sid, goods_nomenclature_item_id, producline_suffix as productline_suffix,
        null as ancestry_array, null as leaf from goods_nomenclatures gn 
        where producline_suffix = '80' and goods_nomenclature_item_id = %s and validity_end_date is null
        order by 2;
        """
        params = [
            self.commodity_code,
            self.commodity_code
        ]
        rows = d.run_query(sql.replace("\n", ""), params)
        self.descendants = []
        if rows:
            for row in rows:
                if 1 > 0:
                # if row[1] != self.commodity_code:
                    self.descendants.append(row[0])
        else:
            self.reason = "Record in document, but does not exist"
        a = 1
        
    def as_dict(self):
        s = {
            "origin": self.origin,
            "country": self.country,
            "reason": self.reason,
            "scope": self.scope,
            "commodity_code": self.commodity_code,
            "measure_type_id": self.measure_type_id,
            "fta_duty_value": self.fta_duty_value,
            "db_duty_value": self.db_duty_value,
            "descendants": self.descendants,
            "entity_type": self.entity_type,
            "significant_digits": self.significant_digits,
            "differences": [],
            "comm_code_differences": [],
            "ignore": False
        }
        return s
