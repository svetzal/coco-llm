import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from generate_cards import Card, Row, render_html


def make_card(title: tuple[str, str], row_count: int = 2) -> Card:
    rows = tuple(
        Row(
            token=f"WORD{index}",
            faces=1,
            first=index,
            last=index,
            exact_percent=5.0,
            printed_percent=5.0,
        )
        for index in range(1, row_count + 1)
    )
    return Card(
        context=title,
        rows=rows,
        suppressed_boundary=False,
        dropped_tokens=0,
        dropped_percent=0.0,
    )


def test_html_renders_four_landscape_cards_per_letter_sheet() -> None:
    cards = [make_card(("#", f"WORD{index}")) for index in range(5)]

    rendered = render_html(cards, faces=20, label="TEST DECK", accent="#25c925")

    assert "@page { size: letter landscape" in rendered
    assert rendered.count('<div class="sheet">') == 2
    assert rendered.count('<div class="card">') == 5


def test_html_makes_context_primary_and_moves_brand_to_footer() -> None:
    rendered = render_html(
        [make_card(("#", "TANDY"))],
        faces=20,
        label="TEST DECK",
        accent="#25c925",
    )

    assert '<p class="ctx">#  TANDY</p>' in rendered
    assert "1 · Current context" in rendered
    assert "2 · Roll" in rendered
    assert '<span class="brand-name">CoCo LLM · Be the model</span>' in rendered
    assert rendered.index('<p class="ctx">') < rendered.index('class="brand-name"')


def test_html_uses_compact_rows_only_for_dense_distributions() -> None:
    normal = render_html(
        [make_card(("#", "TANDY"), row_count=9)], 20, "TEST", "#25c925"
    )
    dense = render_html(
        [make_card(("#", "SINCLAIR"), row_count=10)], 20, "TEST", "#25c925"
    )

    assert '<table class="distribution">' in normal
    assert '<table class="distribution dense">' in dense
