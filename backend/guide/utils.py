import openpyxl
from django.core.files.uploadedfile import UploadedFile


class ExcelParser:
    class COLS:
        CATEGORY = 0
        CODE = 1
        NAME = 2
        COST = 3

    def __init__(self, file: UploadedFile) -> None:
        self.file = file

    def parse(self, from_row: int) -> list[dict]: 
        workbook = openpyxl.load_workbook(self.file)
        sheet = workbook.active
        data = []

        for row in sheet.iter_rows(min_row=from_row, values_only=True):
            if row:
                data.append({
                    'category': row[self.COLS.CATEGORY],
                    'code': row[self.COLS.CODE],
                    'name': row[self.COLS.NAME],
                    'cost': row[self.COLS.COST],
                })
        return data