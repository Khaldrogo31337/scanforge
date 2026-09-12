import argparse
import pathlib
import barcode
import barcode.writer
from barcode.writer import ImageWriter
import sys
import qrcode
import pathvalidate


supported_formats = ["code128", "qrcode", "code39", "ean13", "ean8", "upca", "isbn13", "isbn10", "itf", "pzn", "qr", "list"]

def parse_args():

    parser = argparse.ArgumentParser(description="Scanforge barcode generator")
    parser.add_argument("--value", type=str, default="", help="Barcode value")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("./output/"), help="Output directory")
    parser.add_argument("--format", type=str, default="code128", help="Barcode format (use 'list' to see all options)", choices=supported_formats)
    args = parser.parse_args()
    return args

def main():
    try:
        args = parse_args()
        
        if args.format == "list":
            print(supported_formats)
            return
        if args.format != "list" and args.value == "":
            print("Error: Please provide a value for the barcode.")
            sys.exit(1)
        if args.format == "qr" or args.format == "qrcode":
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(args.value)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            output_dir = args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            sanitized_value = pathvalidate.sanitize_filename(args.value)
            output_path = output_dir / f"{sanitized_value}_{args.format}.png"
            img.save(output_path)
            return
        else:
            output_dir = args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            sanitized_value = pathvalidate.sanitize_filename(args.value)
            output_path = output_dir / f"{sanitized_value}_{args.format}"
            barcode_class = barcode.get_barcode_class(args.format)
            barcode_instance = barcode_class(args.value, writer=ImageWriter())
            barcode_instance.save(str(output_path))
            return
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
