from dataclasses import replace
import re
import classes.globals as g
from classes.database import Database


class Classification(object):
    """
    (1) goods_nomenclature_item_id
    (2) description
    """

    def __init__(self, goods_nomenclature_item_id, description, number_indents = None):
        self.goods_nomenclature_item_id = goods_nomenclature_item_id
        self.description = description
        self.number_indents = number_indents
        self.cleanse()
        
    def cleanse(self):
        if self.goods_nomenclature_item_id == "1515605100":
            a = 1
        self.description = self.description.strip()
        self.description = self.description.replace("-", "- ")
        self.description = self.description.replace("\n", "")
        self.description = self.description.replace("<br>", "")
        self.description = self.description.replace("\xa0", " ")
        # self.description = self.description.replace("   ", " ")
        # self.description = self.description.replace("  ", " ")
        self.description = re.sub(r":$", '', self.description)
        self.description = re.sub(r"\s+", ' ', self.description)
        self.description = self.description.replace(" %", "%")
        self.description = self.description.replace(" kg", "kg")
        self.description = self.description.replace("inkg", "in kg")
        self.description = self.description.replace(" cm", "cm")
        self.description = self.description.replace(" mm", "mm")
        self.description = self.description.replace(" MW", "MW")
        self.description = self.description.replace("litres", " litres")
        self.description = self.description.replace("<sup>", "")
        self.description = self.description.replace("</sup>", "")
        self.description = self.description.replace("<sub>", "")
        self.description = self.description.replace("</sub>", "")
        self.description = re.sub(r"\s+", ' ', self.description)
        self.description = re.sub(r" g$", 'g', self.description)
        self.description = re.sub(r" g, ", "g, ", self.description)
        self.description = re.sub(r" g ", "g ", self.description)
        if self.number_indents is None:
            self.get_indents()
        
    def get_indents(self):
        self.number_indents = 0
        tmp = self.description
        found = True
        while found:
            if tmp[0:2] == "- ":
                self.number_indents += 1
                tmp = tmp[2:]
            else:
                found = False
                
        self.description = tmp.strip()
