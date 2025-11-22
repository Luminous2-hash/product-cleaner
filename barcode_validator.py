from pathlib import Path
import pyexcel as pe
import barcodenumber as bn
import config

def barcode_validator(barcode: str):
    ''' A function to test barcode agains different barcode standards '''
    result = False
    if bn.check_code_ean13(barcode):
        result = True
    elif bn.check_code_ean8(barcode):
        result = True
    elif bn.check_code_upc(barcode):
        result = True
    elif bn.check_code_gs1_datamatrix(barcode):
        result = True
    return result

# The export of all darian products
darian_products = Path(config.darian_products_path)

# Reading products using pyexcel API
records = pe.get_records(file_name = darian_products)

# Evaluating barcodes and storing them into a list
invalid = []
valid = []
for r in records:
        if not barcode_validator(r["بارکد"]):
            invalid.append(r)
        else:
             valid.append(r)

# Saving valid and invalid barcodes to xlsx document
pe.save_as(array=[list(invalid[0].keys())] + [list(r.values()) for r in invalid], dest_file_name="invalid_products.xlsx")
pe.save_as(array=[list(valid[0].keys())] + [list(r.values()) for r in valid], dest_file_name="valid_products.xlsx")