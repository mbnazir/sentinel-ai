from app.connectors.quartz.rest import QuartzConnectorConfig

def test_quartz_connector_secure_defaults():
    c=QuartzConnectorConfig(base_url="https://quartz.example.test")
    assert c.verify_tls is True
    assert c.timeout_seconds==30.0
    assert c.page_size==500
