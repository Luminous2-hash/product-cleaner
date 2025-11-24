from pathlib import Path
import pyexcel as pe
import barcodenumber as bn
import config
from pony import orm

db_address = Path("./database.sqlite")


def barcode_validator(barcode: str):
    """A function to test barcode agains different barcode standards"""
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
records = pe.get_records(file_name=darian_products)

# Evaluating barcodes and storing them into a list
invalid = []
valid = []
for r in records:
    if not barcode_validator(r["بارکد"]):
        invalid.append(r)
    else:
        valid.append(r)

# Saving valid and invalid barcodes to xlsx document
pe.save_as(
    array=[list(invalid[0].keys())] + [list(r.values()) for r in invalid],
    dest_file_name="invalid_products.xlsx",
)
pe.save_as(
    array=[list(valid[0].keys())] + [list(r.values()) for r in valid],
    dest_file_name="valid_products.xlsx",
)

db = orm.Database()

entities = {}

# Dynamically creates database tables out of data in config
for item in config.data:
    table_name = item["name"]

    attrs = {
        "__table__": table_name,  # table name in DB
        "barcode": orm.Required(str),  # barcode
        "name": orm.Required(str),
    }

    entity = type(table_name, (db.Entity,), attrs)
    entities[table_name] = entity


db.bind(provider="sqlite", filename="database.sqlite", create_db=True)
orm.sql_debug(True)
db.generate_mapping(create_tables=True)

if not db_address.exists():
    with orm.db_session:
        for item in config.data:
            entity = entities[item["name"]]

            data_path = Path(config.data_path) / item["file_name"]
            temp_records = pe.get_records(file_name=data_path)

            for r in temp_records:
                try:
                    entity(
                        barcode=str(r[item["barcode_header"]]),
                        name=str(r[item["name_header"]]),
                    )
                except orm.core.CacheIndexError:
                    pass

renamed = []
not_renamed = []

with orm.db_session:
    for r in valid:
        for d in config.data:
                entity = entities[d["name"]]
                query = entity.get(barcode=r["بارکد"])
                if query:
                    temp_r = r
                    temp_r[d["name_header"]] = query.name
                    temp_r["ردیف"] = len(renamed)+1
                    renamed.append(temp_r)
                    break
                else:
                    not_renamed.append(r)

pe.save_as(
    array=[list(renamed[0].keys())] + [list(r.values()) for r in renamed],
    dest_file_name="renamed_products.xlsx",
)