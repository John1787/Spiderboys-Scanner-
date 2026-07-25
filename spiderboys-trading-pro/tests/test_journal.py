from pathlib import Path
import tempfile

from core.data import JOURNAL_COLUMNS, append_journal, load_journal


def test_journal_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "data").mkdir()
        record = {column: "" for column in JOURNAL_COLUMNS}
        record.update({"date": "2026-07-25", "ticker": "SOUN", "pnl": 125.0, "r_multiple": 1.0})
        append_journal(base, record)
        journal = load_journal(base)
        assert len(journal) == 1
        assert journal.iloc[0]["ticker"] == "SOUN"
