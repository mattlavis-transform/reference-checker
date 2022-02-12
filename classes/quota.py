from dataclasses import replace
import re
import classes.globals as g
from classes.database import Database


class Quota(object):
    """
    (1) Quota Number
    (2) Commodity Code
    (3) Country of Origin
    (4) Quota Duty Rate
    (5) Quota Volume
    (6) Date Quota Opens
    (7) Date Quota Closes
    (8) 2021 Quota Volume
    """

    def __init__(self):
        self.quota_order_number_id = ""
        self.commodity_string = ""
        self.commodities = []
        self.origin = ""
        self.quota_duty_rate = ""
        self.quota_volume = None
        self.quota_open_date = ""
        self.quota_close_date = ""
        self.quota_volume_2021 = None

    def cleanse(self):
        self.quota_order_number_id = self.quota_order_number_id.replace(".", "")
        self.quota_order_number_id = self.quota_order_number_id.split("\n")[0]
        self.quota_order_number_id = self.quota_order_number_id.strip()
        self.cleanse_origin()
        self.cleanse_volume()
        self.cleanse_duty()
        
    def cleanse_origin(self):
        replacements = [
            { "from": "USA", "to": "United States" },
            { "from": "Countries other than Member States of the European Union", "to": "ERGA OMNES" },
            { "from": "", "to": "ERGA OMNES" },
            { "from": "Other Non-WTO member countries", "to": "Countries not members of the WTO" }
        ]
        for replacement in replacements:
            if self.origin == replacement["from"]:
                self.origin = replacement["to"]

    def check_validity(self):
        if "05" in self.quota_order_number_id:
            self.valid = True
        else:
            self.valid = False
            
    def cleanse_volume(self):
        self.quota_volume = self.quota_volume.split("This quota")[0]
        self.quota_volume = self.quota_volume.split("This quantity")[0]
        if self.quota_order_number_id in ("052012", "052105", "052106"):
            self.quota_volume = 13335000
        else:
            numeric_filter = filter(str.isdigit, self.quota_volume)
            self.quota_volume = "".join(numeric_filter)
            try:
                self.quota_volume = int(self.quota_volume)
            except:
                self.quota_volume = 0
            
    def cleanse_duty(self):
        self.quota_duty_rate_string = self.quota_duty_rate_string.split("Where")[0]

    def get_commodities(self):
        self.commodity_string = self.commodity_string.replace(" ", "")
        self.commodities = self.commodity_string.split("\n")
        self.commodities = sorted(self.commodities)
        if self.commodities:
            for i in range(len(self.commodities) - 1, -1, -1):
                if self.commodities[i] == "":
                    self.commodities.pop(i)

    def get_duties(self):
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("per", "/")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("£ ", "£")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace(" kg", "kg")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace(" hl", " HLT")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("1000kg", "TNE")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("100kg", "DTN")
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("Zero", "0.00%")
        
        if self.quota_order_number_id == "050067":
            a = 1
            
        self.quota_duty_rate_string = " " + self.quota_duty_rate_string
        self.quota_duty_rate_string = re.sub(r'([^\.])([0-9]{1,3}.[0-9])\%', r'\1\2|%', self.quota_duty_rate_string)
        # self.quota_duty_rate_string = re.sub(r'([^\.])([0-9]{1,3})\%', r'\1\2.00%', self.quota_duty_rate_string)
        self.quota_duty_rate_string = re.sub(r'([^\.0123456789])([0-9]{1,3})\%', r'\1\2.00%', self.quota_duty_rate_string)
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("|", "0")
        self.quota_duty_rate_string = self.quota_duty_rate_string.strip()
        self.quota_duty_rate_string = self.quota_duty_rate_string.replace("0.00.00%", "0.00%")
        
        
        self.duties = self.quota_duty_rate_string.split("\n")
        if self.duties:
            for i in range(len(self.duties) - 1, -1, -1):
                if self.duties[i] == "":
                    self.duties.pop(i)
        else:
            a = 1
        a = 1

    def validate(self):
        print("Validating quota {0}".format(self.quota_order_number_id))
        self.validate_commodities()
        self.validate_origin()
        self.validate_initial_volume()
        self.validate_duties()

    def validate_commodities(self):
        if self.quota_order_number_id in g.app.quota_commodities_dict:
            tmp = g.app.quota_commodities_dict[self.quota_order_number_id]
            self.commodities_db = []
            for measure in tmp:
                self.commodities_db.append(measure["goods_nomenclature_item_id"])
        else:
            self.commodities_db = []

        if self.commodities != self.commodities_db:
            self.write_log("Incorrect commodity code list on quota {0}: {1} on the document versus {2} in the database".format(self.quota_order_number_id, ', '.join(self.commodities), ', '.join(self.commodities_db)))
            pass

    def validate_origin(self):
        if self.quota_order_number_id in g.app.quota_origins_dict:
            origins = g.app.quota_origins_dict[self.quota_order_number_id]
            self.origins_db = []
            for origin in origins:
                self.origins_db.append(origin["geographical_area_description"])
                a = 1
        else:
            self.origins_db = []

        if "other than" not in self.origin.lower():
            if len(self.origins_db) == 1:
                if self.origin != self.origins_db[0]:
                    self.write_log("Incorrect origin on quota {0}: {1} on the document versus {2} in the database".format(self.quota_order_number_id, self.origin, self.origins_db[0]))
                    pass
            elif len(self.origins_db) == 0:
                self.write_log("No origins on quota {0}".format(self.quota_order_number_id))
                pass
            else:
                self.write_log("Multiple origins on quota {0}".format(self.quota_order_number_id))
                pass

    def validate_initial_volume(self):
        if self.quota_order_number_id in g.app.quota_definitions_dict:
            definitions = g.app.quota_definitions_dict[self.quota_order_number_id]
            self.definitions_db = []
            for definition in definitions:
                self.definitions_db.append(definition["initial_volume"])
        else:
            self.definitions_db = []
            
        self.definitions_db = list(set(self.definitions_db))
        if len(self.definitions_db) == 1:
            if self.definitions_db[0] != self.quota_volume:
                self.write_log("Mismatch on quota volume on quota {0}: {1} in the document, {1} in the database".format(self.quota_order_number_id, self.definitions_db[0], self.quota_volume))
                pass

        elif len(self.definitions_db) == 0 and self.quota_order_number_id[0:3] != "054":
            self.write_log("No quota volume on quota {0} in the database".format(self.quota_order_number_id))
            pass
        elif self.quota_order_number_id[0:3] != "054":
            a = 1

    def validate_duties(self):
        if self.quota_order_number_id == "054320":
            a = 1
        if self.quota_order_number_id in g.app.quota_duties_dict:
            duties = g.app.quota_duties_dict[self.quota_order_number_id]
            self.duties_db = []
            for duty in duties:
                self.duties_db.append(duty["duty"])
        else:
            self.duties_db = []
            
        if len(self.duties) == 1:
            self.duties_db = list(set(self.duties_db))
            
        if self.duties != self.duties_db:
            self.write_log("Mismatch on duties on quota {0} in the database. Duties are {1} in the document, but {2} in the database".format(self.quota_order_number_id, ', '.join(self.duties), ', '.join(self.duties_db)))
            a = 1
        else:
            a = 1
        a = 1

    def write_log(self, msg):
        msg = "Error on quota {0}: {1}".format(self.quota_order_number_id, msg)
        f = open(g.app.quotas_log, "a")
        f.write(msg + "\n")
        f.close()
