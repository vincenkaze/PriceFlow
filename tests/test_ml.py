import pytest
from modules.ml.classifier import DemandClassifier
from modules.ml.regressor import DemandRegressor


class TestDemandClassifier:
    @pytest.fixture
    def classifier(self):
        return DemandClassifier()

    def test_classify_high_threshold(self, classifier):
        assert classifier.classify(85) == "HIGH"
        assert classifier.classify(70) == "HIGH"
        assert classifier.classify(100) == "HIGH"

    def test_classify_medium_threshold(self, classifier):
        assert classifier.classify(55) == "MEDIUM"
        assert classifier.classify(40) == "MEDIUM"

    def test_classify_low_threshold(self, classifier):
        assert classifier.classify(30) == "LOW"
        assert classifier.classify(10) == "LOW"
        assert classifier.classify(0) == "LOW"

    def test_analyze_empty_history(self, classifier):
        result = classifier.analyze([])
        assert result['level'] == "LOW"
        assert result['ema'] == 0.0
        assert result['sample_size'] == 0

    def test_analyze_single_point(self, classifier):
        result = classifier.analyze([50])
        assert result['level'] == "MEDIUM"
        assert result['ema'] == 50.0
        assert result['raw_avg'] == 50.0
        assert result['sample_size'] == 1

    def test_analyze_multiple_points(self, classifier):
        result = classifier.analyze([10, 20, 30, 80, 90])
        assert result['sample_size'] == 5
        assert result['raw_avg'] == 46.0
        assert result['ema'] > result['raw_avg']
        assert result['level'] == "MEDIUM"

    def test_predict(self, classifier):
        X = [85, 50, 20]
        predictions = classifier.predict(X)
        assert list(predictions) == ["HIGH", "MEDIUM", "LOW"]


class TestDemandRegressor:
    @pytest.fixture
    def regressor(self):
        return DemandRegressor()

    def test_analyze_trend_insufficient_data(self, regressor):
        result = regressor.analyze_trend([])
        assert result['trend'] == "insufficient_data"
        assert result['forecast'] is None

        result = regressor.analyze_trend([50])
        assert result['trend'] == "insufficient_data"

        result = regressor.analyze_trend([50, 60])
        assert result['trend'] == "insufficient_data"

    def test_analyze_trend_rising(self, regressor):
        result = regressor.analyze_trend([20, 30, 40, 50, 60])
        assert result['trend'] == "rising"
        assert result['velocity'] > 0

    def test_analyze_trend_falling(self, regressor):
        result = regressor.analyze_trend([60, 50, 45, 40, 35])
        assert result['trend'] == "falling"
        assert result['velocity'] < 0

    def test_analyze_trend_stable(self, regressor):
        result = regressor.analyze_trend([50, 52, 48, 51, 49])
        assert result['trend'] == "stable"
        assert -1.5 <= result['velocity'] <= 1.5

    def test_analyze_trend_confidence_bounds(self, regressor):
        result = regressor.analyze_trend([10, 20, 30, 80, 90])
        assert 0 <= result['confidence'] <= 1

    def test_get_chart_data_empty(self, regressor):
        result = regressor.get_chart_data([])
        assert result['raw_points'] == []
        assert result['ema_short'] == []
        assert result['ema_long'] == []
        assert result['trend_line'] == []
        assert result['timestamps'] == []

    def test_get_chart_data_structure(self, regressor):
        result = regressor.get_chart_data([10, 20, 30, 40, 50])
        
        assert 'ema_short' in result
        assert 'ema_long' in result
        assert 'raw_points' in result
        assert 'trend_line' in result
        assert 'timestamps' in result
        
        assert len(result['raw_points']) == 5
        assert len(result['ema_short']) == 5
        assert len(result['ema_long']) == 5
        assert len(result['trend_line']) == 5
        assert len(result['timestamps']) == 5

    def test_predict_fallback(self, regressor):
        result = regressor.predict([10, 20, 30])
        assert len(result) == 1
        assert result[0] == pytest.approx(20.0, abs=1)

    def test_predict_empty(self, regressor):
        result = regressor.predict([])
        assert list(result) == [0]

    def test_partial_fit_updates_model(self, regressor):
        scores = [10, 20, 30, 40, 50, 60, 70]
        regressor.partial_fit(scores)
        assert regressor._fitted == True

    def test_predict_next_returns_value(self, regressor):
        scores = [20, 30, 40, 50, 60, 70, 80]
        regressor.partial_fit(scores)
        pred = regressor.predict_next(scores)
        assert pred is not None
        assert isinstance(pred, float)

    def test_predict_next_insufficient_data(self, regressor):
        regressor = DemandRegressor()
        assert regressor.predict_next([10, 20]) is None

    def test_predict_series(self, regressor):
        scores = [20, 30, 40, 50, 60, 70, 80]
        regressor.partial_fit(scores)
        preds = regressor.predict_series(scores, steps=3)
        assert len(preds) == 3

    def test_ml_forecast_in_analyze_trend(self, regressor):
        scores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        regressor.partial_fit(scores)
        result = regressor.analyze_trend(scores)
        assert 'ml_forecast' in result

    def test_ml_forecast_line_in_chart_data(self, regressor):
        scores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        regressor.partial_fit(scores)
        result = regressor.get_chart_data(scores)
        assert 'ml_forecast_line' in result