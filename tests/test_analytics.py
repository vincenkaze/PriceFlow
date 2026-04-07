import pytest
from unittest.mock import MagicMock


class TestAnalyticsService:
    @pytest.fixture
    def analytics_service(self):
        from services.analytics_service import AnalyticsService
        return AnalyticsService()

    def test_get_price_history_returns_list(self, analytics_service):
        mock_ph = MagicMock()
        mock_ph.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = analytics_service.get_price_history(Product=MagicMock(), PriceHistory=mock_ph, product_id=1)
        assert isinstance(result, list)

    def test_get_recent_changes_returns_list(self, analytics_service):
        mock_ph = MagicMock()
        mock_ph.query.order_by.return_value.limit.return_value.all.return_value = []
        
        mock_product = MagicMock()
        mock_product.query.filter.return_value.all.return_value = []
        
        result = analytics_service.get_recent_changes(Product=mock_product, PriceHistory=mock_ph, limit=20)
        assert isinstance(result, list)

    def test_get_price_history_with_records(self, analytics_service):
        from datetime import datetime
        
        mock_record = MagicMock()
        mock_record.timestamp = datetime(2024, 1, 1)
        mock_record.old_price = 100.0
        mock_record.new_price = 110.0
        mock_record.demand_score = 80
        mock_record.stock = 50
        mock_record.change_reason = 'Test'
        
        mock_ph = MagicMock()
        mock_ph.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_record]
        
        result = analytics_service.get_price_history(Product=MagicMock(), PriceHistory=mock_ph, product_id=1)
        assert len(result) == 1
        assert result[0]['old_price'] == 100.0