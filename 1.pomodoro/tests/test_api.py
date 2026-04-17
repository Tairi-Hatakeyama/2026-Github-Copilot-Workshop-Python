"""
Flask API エンドポイントのテスト
"""
import pytest
from datetime import date


@pytest.fixture
def app():
    from app import create_app
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


class TestGetConfig:
    def test_returns_200(self, client):
        assert client.get('/api/config').status_code == 200

    def test_returns_default_config(self, client):
        data = client.get('/api/config').get_json()
        assert data['work_minutes'] == 25
        assert data['break_minutes'] == 5

    def test_response_has_work_minutes(self, client):
        assert 'work_minutes' in client.get('/api/config').get_json()

    def test_response_has_break_minutes(self, client):
        assert 'break_minutes' in client.get('/api/config').get_json()


class TestPutConfig:
    def test_update_config(self, client):
        res = client.put('/api/config', json={'work_minutes': 30, 'break_minutes': 7})
        assert res.status_code == 200
        data = res.get_json()
        assert data['work_minutes'] == 30
        assert data['break_minutes'] == 7

    def test_get_returns_updated_value(self, client):
        client.put('/api/config', json={'work_minutes': 30, 'break_minutes': 7})
        assert client.get('/api/config').get_json()['work_minutes'] == 30

    def test_invalid_work_minutes_returns_400(self, client):
        res = client.put('/api/config', json={'work_minutes': -1, 'break_minutes': 5})
        assert res.status_code == 400

    def test_zero_work_minutes_returns_400(self, client):
        res = client.put('/api/config', json={'work_minutes': 0, 'break_minutes': 5})
        assert res.status_code == 400

    def test_invalid_break_minutes_returns_400(self, client):
        res = client.put('/api/config', json={'work_minutes': 25, 'break_minutes': 'bad'})
        assert res.status_code == 400

    def test_missing_body_returns_400(self, client):
        assert client.put('/api/config', json={}).status_code == 400


class TestGetTodayStats:
    def test_returns_200(self, client):
        assert client.get('/api/stats/today').status_code == 200

    def test_returns_stats_structure(self, client):
        data = client.get('/api/stats/today').get_json()
        for key in ('date', 'completed_work_sessions',
                    'completed_break_sessions', 'focused_minutes'):
            assert key in data

    def test_returns_today_date(self, client):
        data = client.get('/api/stats/today').get_json()
        assert data['date'] == date.today().isoformat()

    def test_initial_counts_are_zero(self, client):
        data = client.get('/api/stats/today').get_json()
        assert data['completed_work_sessions'] == 0
        assert data['focused_minutes'] == 0


class TestPostStatsEvents:
    def test_record_work_completed(self, client):
        res = client.post('/api/stats/events', json={
            'event_type': 'work_completed',
            'completed_at': '2026-04-17T10:30:00',
        })
        assert res.status_code == 201
        assert res.get_json()['status'] == 'recorded'

    def test_record_break_completed(self, client):
        res = client.post('/api/stats/events', json={
            'event_type': 'break_completed',
            'completed_at': '2026-04-17T10:30:00',
        })
        assert res.status_code == 201

    def test_invalid_event_type_returns_400(self, client):
        res = client.post('/api/stats/events', json={
            'event_type': 'invalid_event',
            'completed_at': '2026-04-17T10:30:00',
        })
        assert res.status_code == 400

    def test_invalid_completed_at_returns_400(self, client):
        res = client.post('/api/stats/events', json={
            'event_type': 'work_completed',
            'completed_at': 'not-a-date',
        })
        assert res.status_code == 400

    def test_missing_event_type_returns_400(self, client):
        assert client.post('/api/stats/events', json={}).status_code == 400
