"""Export a trained model to ONNX (fp32 + int8) for browser/transformers.js use.

RUN step (not exercised by tests): requires `pip install -e ".[export]"`.

Usage: python scripts/export_onnx.py --model runs/model/final --out runs/model/onnx
"""
import argparse

from enembert.export.onnx_export import export


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="runs/model/final")
    parser.add_argument("--out", default="runs/model/onnx")
    args = parser.parse_args()

    export(args.model, args.out)
    print(f"exported {args.model} -> {args.out}")


if __name__ == "__main__":
    main()
