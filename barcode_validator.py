from pathlib import Path
import pyexcel as pe
import barcodenumber
import config
from pony import orm


db_address = Path("./database.sqlite")


def barcode_validator(barcode: str):
    """A function to test barcode agains different barcode standards"""
    barcode_formats = ["ean13", "ean8", "upc", "gs1_datamatrix"]
    # Check against barcode formats via loop
    for bf in barcode_formats:
        if barcodenumber.check_code(bf, barcode):
            return True
    else:
        return False

def record_export(record , dest_file: str, range_header: str):
    ''' A helper function to save records with ranges '''
    if range_header and range_header in iter(record[0].keys()):
        for i, r in enumerate(record):
            r[range_header] = i+1
        pe.save_as(records=record, dest_file_name=dest_file)
    else:
        pe.save_as(records=record, dest_file_name=dest_file)


# The export of all darian products
darian_products = Path(config.darian_products_path)

# Reading products using pyexcel API
records = pe.get_records(file_name=darian_products)

def validate_barcodes(export_to_file: bool):
    # Evaluating barcodes and storing them into a list
    invalid = []
    valid = []
    for r in records:
        if not barcode_validator(r["بارکد"]):
            invalid.append(r)
        else:
            valid.append(r)
    if export_to_file:
        record_export(invalid, "invalid_products.xlsx", "ردیف")
        record_export(valid, "valid_products.xlsx", "ردیف")
    else:
        return {
            "invalid": invalid,
            "valid": valid
        }

if config.barcode_validation:
    validate_barcodes()

db = orm.Database()
db.bind(provider="sqlite", filename="database.sqlite", create_db=True)

def entity_generator(db):
    entities = {}

    # Dynamically creates database tables out of data in config
    for item in config.data:
        table_name = item["name"]

        attrs = {
            "__table__": table_name,  # table name in DB
            "barcode": orm.Required(str, unique=True),  # barcode
            "name": orm.Required(str),
        }

        entity = type(table_name, (db.Entity,), attrs)
        entities[table_name] = entity
    db.generate_mapping(check_tables=True, create_tables=True)

    if config.db_generate:
        # Inserting Data
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

    return entities


def rename_products(products_to_rename):
    entities = entity_generator(db)
    renamed = []
    not_renamed = []

    with orm.db_session:
        for r in products_to_rename:
            for d in config.data:
                entity = entities[d["name"]]
                query = entity.get(barcode=r["بارکد"])
                if query:
                    temp_r = r
                    temp_r[d["name_header"]] = query.name
                    renamed.append(temp_r)
                    break
                else:
                    not_renamed.append(r)

    record_export(not_renamed, "not_renamed_products.xlsx", "ردیف")
    record_export(renamed, "renamed_products.xlsx", "ردیف")
    

if config.rename:
    rename_products(
        validate_barcodes(export_to_file=False)["valid"]
    )