import argparse
import io
import pathlib
import re
import sys
import csv
import logging

import barcode
from barcode.writer import ImageWriter, SVGWriter
import openpyxl
import pathvalidate
from PIL import Image
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


supported_formats = ["code128", "qrcode", "code39", "ean13", "ean8", "upca", "isbn13", "isbn10", "itf", "pzn", "qr", "list"]
logging.basicConfig(stream=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser(description="Scanforge barcode generator")
    parser.add_argument("--value", type=str, default="", help="Barcode value")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("./output/"), help="Output directory")
    parser.add_argument("--format", type=str, default="code128", help="Barcode format (use 'list' to see all options)", choices=supported_formats)
    parser.add_argument("--batch-file", type=pathlib.Path, default=None, help="Batch file path (csv or xlsx)")
    parser.add_argument("--fg-colour", type=str, default="#000000", help="Foreground colour")
    parser.add_argument("--bg-colour", type=str, default="#FFFFFF", help="Background colour")
    parser.add_argument("--module-width", type=float, default=0.2, help="Module width")
    parser.add_argument("--module-height", type=float, default=15.0, help="Module height")
    parser.add_argument("--font-size", type=int, default=10, help="Font size")
    parser.add_argument("--output-format", type=str, default="png", choices=["png", "svg", "pdf"], help="Output format")
    parser.add_argument("--text", action=argparse.BooleanOptionalAction, default=True, help="Show text on barcode")
    args = parser.parse_args()
    return args


def validate_colour(colour):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', colour):
        raise ValueError(f"Invalid hex colour: '{colour}'. Expected format: #RRGGBB (e.g. #FF0000)")


def save_as_pdf(image, output_path):
    page_width, page_height = 612, 792
    img_width, img_height = image.size
    x = (page_width - img_width) / 2
    y = (page_height - img_height) / 2
    c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
    c.drawImage(ImageReader(image), x, y, img_width, img_height)
    c.save()


def generate_barcode(value, format, output_dir, filename=None,
                     fg_colour="#000000", bg_colour="#FFFFFF",
                     module_width=0.2, module_height=15.0,
                     show_text=True, font_size=10, output_format="png"):
    validate_colour(fg_colour)
    validate_colour(bg_colour)

    if format == "qr" or format == "qrcode":
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(value)
        qr.make(fit=True)

        if output_format == "svg":
            raise ValueError("SVG output is not supported for QR codes. Use 'png' or 'pdf' instead.")

        img = qr.make_image(fill_color=fg_colour, back_color=bg_colour)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is not None:
            sanitized_value = pathvalidate.sanitize_filename(filename)
        else:
            sanitized_value = pathvalidate.sanitize_filename(value)
            sanitized_value = f"{sanitized_value}_{format}"

        if output_format == "pdf":
            output_path = output_dir / f"{sanitized_value}.pdf"
            buffer = io.BytesIO()
            img.save(buffer)
            buffer.seek(0)
            pil_img = Image.open(buffer)
            save_as_pdf(pil_img, output_path)
        else:
            output_path = output_dir / f"{sanitized_value}.png"
            img.save(output_path)
        return
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is not None:
            sanitized_value = pathvalidate.sanitize_filename(filename)
        else:
            sanitized_value = pathvalidate.sanitize_filename(value)
            sanitized_value = f"{sanitized_value}_{format}"

        writer_options = {
            "module_width": module_width,
            "module_height": module_height,
            "font_size": font_size,
            "write_text": show_text,
            "foreground": fg_colour,
            "background": bg_colour,
        }

        if output_format == "svg":
            writer_instance = SVGWriter()
        else:
            writer_instance = ImageWriter()

        barcode_class = barcode.get_barcode_class(format)
        barcode_instance = barcode_class(value, writer=writer_instance)

        if output_format == "pdf":
            img = barcode_instance.render(writer_options)
            output_path = output_dir / f"{sanitized_value}.pdf"
            save_as_pdf(img, output_path)
        else:
            output_path = output_dir / sanitized_value
            barcode_instance.save(str(output_path), options=writer_options)
        return


def run_batch(batch_file, output_dir, fg_colour, bg_colour, module_width,
              module_height, show_text, font_size, output_format):
    total, success, failed = 0, 0, 0
    if batch_file.suffix == ".csv":
        with open(batch_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = row["value"].strip()
                if value:
                    total += 1
                    try:
                        generate_barcode(
                            value,
                            format=row.get("format", "").strip() or "code128",
                            output_dir=output_dir,
                            filename=row.get("filename", "").strip() or None,
                            fg_colour=fg_colour,
                            bg_colour=bg_colour,
                            module_width=module_width,
                            module_height=module_height,
                            show_text=show_text,
                            font_size=font_size,
                            output_format=output_format,
                        )
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
                    generate_barcode(
                        value,
                        format=row[1].strip() if row[1] else "code128",
                        output_dir=output_dir,
                        filename=row[2].strip() if row[2] else None,
                        fg_colour=fg_colour,
                        bg_colour=bg_colour,
                        module_width=module_width,
                        module_height=module_height,
                        show_text=show_text,
                        font_size=font_size,
                        output_format=output_format,
                    )
                    success += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"Error: {e}")
            else:
                logging.info(f"Empty value")

    else:
        print(f"Unsupported batch file format: {batch_file}")
        return
    print(f"Total: {total}, Success: {success}, Failed: {failed}")


def main():
    try:
        args = parse_args()
        if args.batch_file is not None:
            run_batch(
                args.batch_file, args.output_dir,
                args.fg_colour, args.bg_colour,
                args.module_width, args.module_height,
                args.text, args.font_size, args.output_format,
            )
            return

        if args.format == "list":
            print(supported_formats)
            return

        if args.format != "list" and args.value == "":
            print("Error: Please provide a value for the barcode.")
            sys.exit(1)

        generate_barcode(
            args.value, args.format, args.output_dir,
            fg_colour=args.fg_colour, bg_colour=args.bg_colour,
            module_width=args.module_width, module_height=args.module_height,
            show_text=args.text, font_size=args.font_size,
            output_format=args.output_format,
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
