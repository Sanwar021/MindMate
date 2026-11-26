import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "risk_classifier.py"
SPEC = importlib.util.spec_from_file_location("risk_classifier", MODULE_PATH)
rc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rc)


def test_threshold_is_largest_value_reaching_dev_recall():
    probs = [
        [0.05, 0.05, 0.80, 0.10],
        [0.10, 0.10, 0.30, 0.50],
        [0.70, 0.20, 0.05, 0.05],
    ]
    truth = [2, 3, 0]
    assert rc.choose_threshold(probs, truth, target=0.95) == 0.8


def test_high_recall_threshold_never_uses_risk_argmax_below_threshold():
    probs = [[0.30, 0.35, 0.34, 0.01], [0.05, 0.05, 0.60, 0.30]]
    assert rc.threshold_predictions(probs, 0.8) == [1, 2]


def test_metrics_report_gate_values_and_wilson_interval():
    metrics = rc.classification_metrics([0, 1, 2, 3], [0, 2, 2, 3])
    assert metrics["escalation_recall"] == 1.0
    assert metrics["false_escalation"] == 0.5
    assert metrics["high_predicted_none"] == 0
    assert metrics["high_recall_wilson"][:2] == [1, 1]


def test_missing_message_labels_fail_instead_of_using_conversation_label():
    record = {
        "id": "MM-001-en", "conv_id": "MM-001", "language": "english",
        "risk_label": "high", "messages": [{"role": "user", "content": "hello"}],
    }
    records = [dict(record, id=f"MM-{i:03}-en", conv_id=f"MM-{i:03}") for i in range(250)] * 3
    try:
        rc.build_rows(records)
    except ValueError as error:
        assert "Per-message risk labels are missing" in str(error)
    else:
        raise AssertionError("Missing per-message labels must fail")
