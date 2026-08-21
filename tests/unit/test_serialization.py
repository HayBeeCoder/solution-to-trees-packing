from tree_packing.serialization import format_value, load_submission, parse_value, write_submission


def test_format_round_trip() -> None:
    assert parse_value(format_value(-0.123456)) == -0.123456


def test_parse_tolerates_plain_float() -> None:
    assert parse_value(1.5) == 1.5


def test_write_then_load(tmp_path) -> None:
    solutions = {n: [(0.0, 0.0, 0.0)] * n for n in range(1, 201)}
    out = tmp_path / "sub.csv"
    write_submission(solutions, out)
    df = load_submission(out)
    assert len(df) == 20100
    assert set(df["n"]) == set(range(1, 201))
    row = df[(df["n"] == 3) & (df["tree_idx"] == 2)].iloc[0]
    assert (row["x"], row["y"], row["deg"]) == (0.0, 0.0, 0.0)
