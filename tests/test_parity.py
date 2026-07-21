from pathlib import Path

import pytest

FIXTURES = ["Portanto, o governo deve criar programas, a fim de reduzir o problema.",
            "O tema é discutido há décadas no Brasil.",
            "Cabe ao Ministério da Saúde ampliar o acesso, por meio de mutirões.",
            "Conclui-se, portanto, que medidas são urgentes.",
            "A família precisa acompanhar os jovens, para que os casos diminuam."]


def _onnx_spans(sess, tok, decode, text: str):
    enc = tok(text, return_offsets_mapping=True, return_tensors="np",
              truncation=True, max_length=384)
    offsets = enc.pop("offset_mapping")[0].tolist()
    logits = sess.run(None, {k: v for k, v in enc.items()})[0][0]
    return decode([tuple(o) for o in offsets], logits.argmax(-1).tolist())


@pytest.mark.skipif(not Path("runs/model/onnx/model_quantized.onnx").exists(),
                    reason="run export first")
def test_torch_onnx_span_parity():
    import onnxruntime as ort
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    from enembert.training.predict import decode, predict_spans

    tok = AutoTokenizer.from_pretrained("runs/model/final")
    torch_model = AutoModelForTokenClassification.from_pretrained("runs/model/final")
    fp32_sess = ort.InferenceSession("runs/model/onnx/model.onnx")
    int8_sess = ort.InferenceSession("runs/model/onnx/model_quantized.onnx")

    for text in FIXTURES:
        want = predict_spans(torch_model, tok, text, max_length=384)

        # fp32 must reproduce torch exactly — any drift there is an export bug.
        got_fp32 = _onnx_spans(fp32_sess, tok, decode, text)
        assert got_fp32 == want, f"fp32 ONNX mismatch on: {text!r}"

        # int8 is what the browser downloads. Quantization shifts the odd span
        # boundary (a trailing comma, or an extra short span on the modal "deve"),
        # which is cosmetic. What must NOT drift is the SET OF ELEMENTS found:
        # that is what the checklist shows and what the C5 estimator consumes, so
        # it is the property the product actually depends on.
        got_int8 = _onnx_spans(int8_sess, tok, decode, text)
        assert {s.label for s in got_int8} == {s.label for s in want}, (
            f"int8 found a different element SET on {text!r}: "
            f"{sorted({s.label for s in got_int8})} vs torch {sorted({s.label for s in want})}"
        )
