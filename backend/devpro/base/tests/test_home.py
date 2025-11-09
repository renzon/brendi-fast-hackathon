def test_home_status(client, db):
    resp = client.get('/')
    assert resp.status_code == 200
