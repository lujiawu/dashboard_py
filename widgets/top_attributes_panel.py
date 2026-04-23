import logging
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import RankedItem

logger = logging.getLogger(__name__)


class TopAttributesPanel(VerticalScroll):
    def compose(self):
        yield Static(id="content", expand=True)

    def format_text(self, items: list[RankedItem]) -> str:
        if not items:
            return "No data"

        lines = []
        for item in items:
            bar_width = 30
            filled = int(item.percentage / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"{item.rank:>2}. {item.label:<35} {item.count:>6} {bar}")

        return "\n".join(lines)

    def update_mock_data(self):
        mock_data = [
            RankedItem(1, "rr-web.event", 654, 654),
            RankedItem(2, "rr-web.offset", 654, 654),
            RankedItem(3, "otelSpanID", 410, 654),
            RankedItem(4, "otelTraceID", 410, 654),
            RankedItem(5, "context.total", 278, 654),
            RankedItem(6, "userId", 139, 654),
            RankedItem(7, "app.payment.amount", 83, 654),
            RankedItem(8, "request.amount.units.low", 83, 654),
            RankedItem(9, "request.creditCard.creditCardNumber", 83, 654),
            RankedItem(10, "span_id", 83, 654),
            RankedItem(11, "some extended attribute name", 75, 654),
            RankedItem(12, "another long attribute", 65, 654),
            RankedItem(13, "additional attribute field", 55, 654),
            RankedItem(14, "more attribute data", 45, 654),
            RankedItem(15, "final attribute", 35, 654),
        ]
        content = self.query_one("#content", Static)
        content.update(self.format_text(mock_data))
        logger.info(f"[TopAttributesPanel] updated: items={len(mock_data)}, panel_size={self.size}, content_size={content.size}")
