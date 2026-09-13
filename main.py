import argparse
from fileinput import filename
import pathlib
from profile import run
import barcode
import barcode.writer
from barcode.writer import ImageWriter
import sys
import qrcode
import pathvalidate
import csv
import openpyxl 
import logging

supported_formats = ["code128", "qrcode", "code39", "ean13", "ean8", "upca", "isbn13", "isbn10", "itf", "pzn", "qr", "list"]
logging.basicConfig(stream=sys.stderr)
def parse_args():
    parser = argparse.ArgumentParser(description="Scanforge barcode generator")
    parser.add_argument("--value", type=str, default="", help="Barcode value")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("./output/"), help="Output directory")
    parser.add_argument("--format", type=str, default="code128", help="Barcode format (use 'list' to see all options)", choices=supported_formats)
    parser.add_argument("--batch-file", type=pathlib.Path, default=None, help="Batch file path (csv or xlsx)",)
    args = parser.parse_args()
    return args
def generate_barcode(value, format, output_dir, filename=None):
    if format == "qr" or format == "qrcode":
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        output_dir.mkdir(parents=True, exist_ok=True)
        if filename is not None:
            sanitized_value = pathvalidate.sanitize_filename(filename)
            output_path = output_dir / f"{sanitized_value}.png"

        else:
            sanitized_value = pathvalidate.sanitize_filename(value)
            output_path = output_dir / f"{sanitized_value}_{format}.png"
        img.save(output_path)
        return
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is not None:
            #sanitized_value = filename
            sanitized_value = pathvalidate.sanitize_filename(filename)
            output_path = output_dir / f"{sanitized_value}"
        else:
            sanitized_value = pathvalidate.sanitize_filename(value)
            output_path = output_dir / f"{sanitized_value}_{format}"
        barcode_class = barcode.get_barcode_class(format)
        barcode_instance = barcode_class(value, writer=ImageWriter())
        barcode_instance.save(str(output_path))
        return
        
def run_batch(batch_file, output_dir):
    total, success, failed = 0, 0, 0
    if batch_file.suffix == ".csv":
        with open(batch_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = row["value"].strip()
                if value:
                    total += 1
                    try:
                        generate_barcode(value, format = row.get("format", "").strip() or "code128", output_dir=output_dir, filename = row.get("filename", "").strip() or None)
                        success += 1
                    except Exception as e:
                        failed += 1
                        logging.error(f"Error: {e}")
                else:
                    logging.info(f"Empty value: {value}")
    
    elif batch_file.suffix == ".xls" or batch_file.suffix == ".xlsx":
        workbook = openpyxl.load_workbook(batch_file)
        sheet = workbook.active
        for row in sheet.iter_rows(values_only=True, min_row=2):
            value = row[0].strip() if row[0] else None
            if value:
                total += 1
                try:
                    #value = row[0].strip() if row[0] else None
                    generate_barcode(value, format = row[1].strip() if row[1] else "code128", output_dir=output_dir, filename = row[2].strip() if row[2] else None)
                    success += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"Error: {e}")
            else:
                logging.info(f"Empty value")
    #print(f"Total: {total}, Success: {success}, Failed: {failed}")

    else:
        print(f"Unsupported batch file format: {batch_file}")
        return
    print(f"Total: {total}, Success: {success}, Failed: {failed}")


def main():
    try:
        args = parse_args()
        if args.batch_file is not None:
            run_batch(args.batch_file, args.output_dir)
            return
            
        if args.format == "list":
            print(supported_formats)
            return
            
        if args.format != "list" and args.value == "":
            print("Error: Please provide a value for the barcode.")
            sys.exit(1)
        
        generate_barcode(args.value, args.format, args.output_dir)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
