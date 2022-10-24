import pytest
from util import mock_process_message
import asyncio
from unittest.mock import Mock

from l3_atom.off_chain import Kraken


@pytest.mark.asyncio()
async def test_kraken_connector(teardown_async):
    types = ['trade', 'book', 'ticker', 'ohlc']
    ret = []
    Kraken.process_message = mock_process_message(ret)
    Kraken._init_kafka = Mock()
    connector = Kraken()
    loop = asyncio.get_event_loop()
    connector.start(loop)
    while len(ret) < 10:
        await asyncio.sleep(0.1)
    for msg in ret:
        print(msg)
        assert (isinstance(msg, dict) and 'status' in msg) or any(msg[-2].startswith(t) for t in types)
    await connector.stop()