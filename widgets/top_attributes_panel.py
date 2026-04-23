from textual.widgets import Static
from models.types import RankedItem


class TopAttributesPanel(Static):
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
        ]
        self.update(self.format_text(mock_data))
