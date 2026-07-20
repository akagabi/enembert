"""Export a trained token-classification model to ONNX (fp32 + dynamic int8).

Uses `optimum.exporters.onnx` (subprocess CLI) to produce `model.onnx` plus
tokenizer files in transformers.js-compatible layout, then quantizes to
`model_quantized.onnx` with onnxruntime's dynamic quantization.
"""
import subprocess
import sys
from pathlib import Path

from onnxruntime.quantization import QuantType, quantize_dynamic


def export(model_dir: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "optimum.exporters.onnx",
         "--model", model_dir, "--task", "token-classification", str(out)],
        check=True,
    )
    quantize_dynamic(out / "model.onnx", out / "model_quantized.onnx",
                      weight_type=QuantType.QInt8)
