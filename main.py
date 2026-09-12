import argparse
import pathlib
import barcode
import barcode.writer
from barcode.writer import ImageWriter
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Scanforge barcode generator")
    parser.add_argument("--value", type=str, default="", help="Barcode value", required=True)
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("./output/"), help="Output directory")
    args = parser.parse_args()
    return args

def main():
    try:
        args = parse_args()
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        value = args.value
        barcode_class = barcode.get_barcode_class("code128")
        barcode_instance = barcode_class(value, writer=ImageWriter())
        output_path = output_dir / f"{value}_code128"
        barcode_instance.save(str(output_path))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
