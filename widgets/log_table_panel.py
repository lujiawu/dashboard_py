from textual.widgets import DataTable
from models.types import LogEntry


class LogTablePanel(DataTable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zebra_stripes = True

    def on_mount(self):
        self.cursor_type = "row"
        self.add_columns("Time", "Level", "Host", "Service", "Message")
        self.add_rows(self._get_mock_data())

    def _get_mock_data(self) -> list[list[str]]:
        return [
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "GetCartAsync called with userId={userId}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "GetCartAsync called with userId={userId}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "GetCartAsync called with userId={userId}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "GetCartAsync called with userId={userId}"],
            ["12:22:08", "INFO", "08b51e8316c6", "cart", "AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}"],
            ["12:22:08", "INFO", "", "recommendation", "Receive ListRecommendations for product ids:['HQ7GWGPNH4', 'OLJCESPC7Z', 'L9ECAV7KIM', 'LS4P..."],
            ["12:22:08", "INFO", "", "recommendation", "Receive ListRecommendations for product ids:['OLJCESPC7Z', '1YMWWN1N40', '6E92ZMYYFZ', '9SIQ..."],
            ["12:22:08", "INFO", "", "recommendation", "Receive ListRecommendations for product ids:['L9ECAV7KIM', '2ZYFJ3GM2N', 'LS4PSXUNUM', '66VC..."],
            ["12:22:08", "INFO", "ac46c7f5cce6", "kafka", "[LocalLog partition=__cluster_metadata-0, dir=/tmp/kafka-logs] Rolled new log segment at off..."],
            ["12:22:08", "INFO", "ac46c7f5cce6", "kafka", "[ProducerStateManager partition=__cluster_metadata-0] Wrote producer snapshot at offset 1714..."],
            ["12:22:08", "INFO", "e81ca6c9d7b5", "payment", "Charge request received."],
            ["12:22:08", "ERROR", "e81ca6c9d7b5", "payment", "Visa cache full: cannot add new item."],
            ["12:22:08", "INFO", "", "currency", "Convert conversion successful"],
            ["12:22:08", "INFO", "", "currency", "Convert conversion successful"],
            ["12:22:13", "INFO", "ab25f780f642", "ad", "no baggage found in context"],
            ["12:22:13", "INFO", "ab25f780f642", "ad", "Targeted ad request received for [telescopes, books, accessories]"],
            ["12:22:13", "INFO", "20bdc678616d", "quote", "Calculated quote"],
            ["12:22:13", "INFO", "20bdc678616d", "quote", "Calculated quote"],
        ]
