import pytest
from datetime import datetime
from unittest.mock import mock_open, patch
from Processing_the_log_file import LogAnalyzer
import json
import argparse


# Фикстуры для тестов
@pytest.fixture
def sample_logs():
    return [
        json.dumps({
            "@timestamp": "2023-01-01T12:00:00+00:00",
            "url": "/api/users",
            "response_time": 150
        }),
        json.dumps({
            "@timestamp": "2023-01-01T12:01:00+00:00",
            "url": "/api/products",
            "response_time": 200
        }),
        json.dumps({
            "@timestamp": "2023-01-02T12:00:00+00:00",
            "url": "/api/users",
            "response_time": 100
        })
    ]


@pytest.fixture
def analyzer():
    return LogAnalyzer()


# Тесты для load_logs
def test_load_logs(analyzer, sample_logs):
    with patch("builtins.open", mock_open(read_data="\n".join(sample_logs))):
        logs = analyzer.load_logs(["dummy.log"])
        assert len(logs) == 3
        assert logs[0]["url"] == "/api/users"


def test_load_logs_with_date_filter(analyzer, sample_logs):
    with patch("builtins.open", mock_open(read_data="\n".join(sample_logs))):
        logs = analyzer.load_logs(["dummy.log"], filter_date="2023-01-01")
        assert len(logs) == 2
        assert all("/api/products" in [log["url"] for log in logs] or
                   "/api/users" in [log["url"] for log in logs] for log in logs)


def test_load_logs_invalid_json(analyzer, sample_logs):
    corrupt_data = sample_logs + ["invalid json"]
    with patch("builtins.open", mock_open(read_data="\n".join(corrupt_data))):
        logs = analyzer.load_logs(["dummy.log"])
        assert len(logs) == 3


# Тесты для generate_average_report
def test_generate_average_report(analyzer):
    test_logs = [
        {"url": "/api/users", "response_time": 100},
        {"url": "/api/users", "response_time": 200},
        {"url": "/api/products", "response_time": 50}
    ]

    report = analyzer.generate_average_report(test_logs)
    assert len(report) == 2
    assert report[0][0] == "/api/users"
    assert report[0][1] == 2
    assert report[0][2] == "150.00 ms"
    assert report[1][0] == "/api/products"


# Тесты для parse_args
def test_parse_args(analyzer):
    test_args = ["--file", "access.log", "--report", "average"]
    with patch("argparse.ArgumentParser.parse_args",
               return_value=argparse.Namespace(file=["access.log"], report="average", date=None)):
        args = analyzer.parse_args()
        assert args.file == ["access.log"]
        assert args.report == "average"


# Тесты для generate_report
def test_generate_report_unknown_type(analyzer):
    with pytest.raises(ValueError, match="Unknown report type: unknown"):
        analyzer.generate_report("unknown", [])


# Тесты для основного выполнения
def test_run_with_no_logs(analyzer, capsys):
    # Мокируем все зависимости
    with patch.object(analyzer, 'parse_args') as mock_parse, \
            patch.object(analyzer, 'load_logs', return_value=[]), \
            patch.object(analyzer, 'generate_report') as mock_report:
        # Настраиваем mock для parse_args
        mock_args = argparse.Namespace(
            file=["access.log"],
            report="average",
            date=None
        )
        mock_parse.return_value = mock_args

        # Вызываем тестируемый метод
        analyzer.run()

        # Проверяем вывод
        captured = capsys.readouterr()
        assert "No log entries found" in captured.out
        mock_report.assert_not_called()  # Проверяем, что генерация отчета не вызывалась


def test_run_with_logs(analyzer, capsys):
    test_logs = [{"url": "/test", "response_time": 100}]
    with patch.object(analyzer, 'load_logs', return_value=test_logs), \
            patch.object(analyzer, 'parse_args', return_value=argparse.Namespace(
                file=["access.log"], report="average", date=None)):
        analyzer.run()
        captured = capsys.readouterr()
        assert "Endpoint" in captured.out
        assert "/test" in captured.out