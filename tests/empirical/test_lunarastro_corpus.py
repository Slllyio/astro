"""LunarAstro -> ChartRow adapter: composition, not modification, of build_banks."""

from __future__ import annotations

from app.empirical.tournament.lunarastro_corpus import read_lunarastro_corpus


def test_categories_join_into_a_sorted_semicolon_label(tmp_path):
    """label carries every category, order-independent of the source file."""
    csv_text = (
        "source_id,name,birth_year,birth_month,birth_day,birth_hour_local,"
        "birth_minute,birth_second,tz_offset,birth_ut_hour,latitude,longitude,"
        "categories,time_is_placeholder,time_tier,data_quality,source_url\n"
        "lunar_x,X,1950,1,1,8,0,0,0.0,8.0,10.0,10.0,Writers;Vocation,false,A,ok,u\n"
    )
    raw = tmp_path / "corpus.csv"
    raw.write_text(csv_text, encoding="utf-8")
    rows = read_lunarastro_corpus(raw)
    assert len(rows) == 1
    assert rows[0].label == "Vocation;Writers"
    assert rows[0].person_id == "lunar_x"
    assert rows[0].time_tier == "A"


def test_no_categories_yields_empty_label(tmp_path):
    csv_text = (
        "source_id,name,birth_year,birth_month,birth_day,birth_hour_local,"
        "birth_minute,birth_second,tz_offset,birth_ut_hour,latitude,longitude,"
        "categories,time_is_placeholder,time_tier,data_quality,source_url\n"
        "lunar_y,Y,1950,1,1,8,0,0,0.0,8.0,10.0,10.0,,false,A,ok,u\n"
    )
    raw = tmp_path / "corpus.csv"
    raw.write_text(csv_text, encoding="utf-8")
    rows = read_lunarastro_corpus(raw)
    assert rows[0].label == ""
