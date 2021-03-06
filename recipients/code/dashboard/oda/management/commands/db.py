import xlrd
import ftypes

class DataProcessingException(Exception):
    pass

class SheetReader(object):
    def __init__(self, sheet):
        self._sheet = sheet
        def get_data():
            for i in range(self._sheet.nrows):
                row = self._sheet.row(i)
                r = map(lambda x : x.value, row)
                yield r
        self._data = ftypes.list(*get_data())

    @property
    def data(self):
        return self._data

class XLSFile(object):
    def __init__(self, file_path, sheet_name):
        self.workbook = xlrd.open_workbook(file_path)
        self.sheet = self.workbook.sheet_by_name(sheet_name)
        self.data = ftypes.list(*self._load_data())

    def _load_data(self):
        for i in range(self.sheet.nrows):
            row = self.sheet.row(i)
            r = map(lambda x : x.value, row)
            yield r

class XLSDB(object):
    def __init__(self, file_path, sheet_name):
        self.file_path = file_path
        self.fileobj = XLSFile(file_path, sheet_name)
        self.data = self.fileobj.data

    def filter_by_country(self, iso3):
        country_data = self.data / (lambda x : x["ISO3"] == iso3)
        return FListMixin(country_data)

class FListMixin(object):
    def __init__(self, data):
        self.data = data

    def filter(self, func):
        return FListMixin(self.data / func)

    def __str__(self):
        return "\n".join(map(str, self.data))

    def __getitem__(self, idx):
        return self.data[idx]

class PurposeDBFactory(XLSDB):
    def __init__(self, file_path="../data/Purpose of ODA.xls", sheet_name="DB"):
        super(PurposeDBFactory, self).__init__(file_path, sheet_name)

class PurposeCommitmentsFactory(XLSDB):
    def __init__(self, file_path="../data/2011_purpose_commitments.xls", sheet_name="DB"):
        super(PurposeDBFactory, self).__init__(file_path, sheet_name)

class ODASourceFactory(XLSDB):
    def __init__(self, file_path="../data/disbursement_sources.xls", sheet_name="Sheet1"):
        super(ODASourceFactory, self).__init__(file_path, sheet_name)

class IndicatorsFactory(XLSDB):
    def __init__(self, file_path="../data/Table1.xls", sheet_name="DB"):
        super(IndicatorsFactory, self).__init__(file_path, sheet_name)

class LargestDisbursementsFactory(XLSDB):
    def __init__(self, file_path="../data/Largest Disbursements.xlsx", sheet_name="ABC"):
        super(LargestDisbursementsFactory, self).__init__(file_path, sheet_name)

class LargestCommitmentsFactory(XLSDB):
    def __init__(self, file_path="../data/Largest Commitments.xlsx", sheet_name="Largest_Commitments DB"):
        super(LargestCommitmentsFactory, self).__init__(file_path, sheet_name)

if __name__ == "__main__":
    osf = LargestCommitmentsFactory()
    print osf.filter_by_country("AFG")
