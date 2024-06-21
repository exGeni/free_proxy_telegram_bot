import os
from import_proxies import *
from handlers import *
from bot import *
from db_utils import *
import pytest
import aiosqlite
from unittest.mock import patch, AsyncMock

# Fixture to mock get_db_path function
@pytest.fixture
async def mock_get_db_path(monkeypatch):
    mock_path = AsyncMock(return_value='path/to/proxies.db')
    monkeypatch.setattr('db_utils.get_db_path', mock_path)
    return mock_path

# Tests for db_utils.py
@pytest.mark.asyncio
async def test_init_db(mock_get_db_path):
    """Test the init_db function.
    The test uses AsyncMock to mock the database connection.
    It patches aiosqlite.connect to return a mock database.
    It checks if execute and commit methods are called once each. """
    mock_db = AsyncMock()
    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        await init_db()
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_active_proxy(mock_get_db_path):
    """Test the get_active_proxy function.
    Mocks the database cursor to return a predefined proxy.
    Checks if the function correctly retrieves and returns the active proxy."""
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = ('http://example.com:8080',)

    mock_db = AsyncMock()
    mock_db.execute.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor))

    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        proxy = await get_active_proxy()

    assert proxy == 'http://example.com:8080'

@pytest.mark.asyncio
async def test_replace_proxy(mock_get_db_path):
    """
    Test the replace_proxy function.
    This test verifies that the function correctly replaces an old proxy with a new one from the database.
    """
    # Mock data that simulates a database record
    mock_db_record = (
        'http://example.com:8080',
        'active',
        True,
        1623456789,
        'high',
        0.5,
        1623400000,
        '192.168.1.1',
        'AS12345',
        'Example ISP',
        'New York',
        'North America',
        'United States',
        'US',
        'Example ISP',
        'Example Organization',
        'New York',
        1623456789,
        8080,
        'http',
        False,
        1.0,
        100,
        0,
        99.9,
        'America/New_York',
        '10001'
    )

    # Set up the mock cursor
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = mock_db_record

    # Set up the mock database connection
    mock_db = AsyncMock()
    mock_db.execute.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor))

    # Patch the database connection
    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        # Call the function we're testing
        new_proxy = await replace_proxy(1234, ['http://old-proxy.com:8080'])

    # Assert that the function returns the correct proxy
    assert new_proxy == 'http://example.com:8080'

    # Verify that the correct SQL query was executed
    mock_db.execute.assert_called_with(
        'SELECT proxy FROM proxies WHERE alive = 1 AND proxy NOT IN (?) ORDER BY RANDOM() LIMIT 1',
        ('http://old-proxy.com:8080',)
    )

    # Test the case when no new proxy is found
    mock_cursor.fetchone.return_value = None
    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        new_proxy = await replace_proxy(1234, ['http://old-proxy.com:8080'])

    # Assert that the function returns None when no new proxy is found
    assert new_proxy is None

    # Verify that the fallback query was executed
    mock_db.execute.assert_called_with(
        'SELECT proxy FROM proxies WHERE alive = 1 ORDER BY RANDOM() LIMIT 1'
    )

@pytest.mark.asyncio
async def test_create_users_table(mock_get_db_path):
    """Test the create_users_table function.
    Similar to test_init_db, it checks if the SQL execution and commit are called."""
    mock_db = AsyncMock()
    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        await create_users_table()
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_main(monkeypatch):
    """Test the main function."""
    # This test checks if the main function initializes the database,
    # creates the users table, fetches and imports proxies, and starts
    # the periodic update process.
    mock_init_db = AsyncMock()
    mock_create_users_table = AsyncMock()
    mock_fetch_proxies = AsyncMock(return_value=[{'proxy': 'http://example.com:8080'}])
    mock_import_proxies = AsyncMock()
    mock_periodic_update = AsyncMock()
    mock_bot = AsyncMock()

    monkeypatch.setattr('db_utils.init_db', mock_init_db)
    monkeypatch.setattr('db_utils.create_users_table', mock_create_users_table)
    monkeypatch.setattr('import_proxies.fetch_proxies', mock_fetch_proxies)
    monkeypatch.setattr('import_proxies.import_proxies', mock_import_proxies)
    monkeypatch.setattr('import_proxies.periodic_update', mock_periodic_update)
    monkeypatch.setattr('telebot.async_telebot.AsyncTeleBot', lambda token: mock_bot)

    # Use asyncio.wait_for to set a timeout for the main function
    try:
        await asyncio.wait_for(main(), timeout=10.0)  # 10 second timeout
    except asyncio.TimeoutError:
        pass  # We expect main to run indefinitely, so a timeout is normal

    # Verify that all necessary functions are called
    mock_init_db.assert_called_once()
    mock_create_users_table.assert_called_once()
    mock_fetch_proxies.assert_called_once()
    mock_import_proxies.assert_called_once_with([{'proxy': 'http://example.com:8080'}])
    assert mock_periodic_update.call_count > 0  # Should be called at least once
    mock_bot.polling.assert_called_once_with(non_stop=True)


@pytest.mark.asyncio
async def test_fetch_proxies(monkeypatch):
    """Test the fetch_proxies function."""
    # This test verifies that the fetch_proxies function correctly
    # retrieves proxy data from the API and returns it.
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {'proxies': [{'proxy': 'http://example.com:8080'}]}

    mock_session = AsyncMock()
    mock_session.get.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

    with patch('aiohttp.ClientSession', return_value=mock_session):
        proxies = await fetch_proxies()

    # Check if the function returns the expected proxy data
    assert proxies == [{'proxy': 'http://example.com:8080'}]

@pytest.mark.asyncio
async def test_import_proxies(mock_get_db_path):
    """Test the import_proxies function."""
    # This test checks if the import_proxies function correctly
    # inserts proxy data into the database.
    mock_db = AsyncMock()
    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        await import_proxies([{'proxy': 'http://example.com:8080'}])
    
    # Verify that execute and commit are called
    mock_db.execute.assert_called()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_callback_query(monkeypatch):
    """Test the callback_query function."""
    # This test verifies that the callback_query function
    # correctly handles different types of callback data.
    mock_call = AsyncMock()
    mock_call.data = '/check_proxy'

    mock_handle_check_proxy = AsyncMock()
    mock_handle_get_proxy = AsyncMock()
    mock_handle_help = AsyncMock()

    monkeypatch.setattr('handlers.handle_check_proxy', mock_handle_check_proxy)
    monkeypatch.setattr('handlers.handle_get_proxy', mock_handle_get_proxy)
    monkeypatch.setattr('handlers.handle_help', mock_handle_help)

    await callback_query(mock_call)

    # Check if the correct handler is called based on the callback data
    mock_handle_check_proxy.assert_called_once_with(mock_call.message)

@pytest.mark.asyncio
async def test_handle_check_proxy(monkeypatch):
    """Test the handle_check_proxy function."""
    # This test verifies that handle_check_proxy correctly retrieves
    # and displays the user's assigned proxies.
    mock_message = AsyncMock()
    mock_message.chat.id = 1234

    mock_get_assigned_proxies_and_language_code = AsyncMock(return_value=([], None))
    mock_bot = AsyncMock()

    monkeypatch.setattr('handlers.get_assigned_proxies_and_language_code', mock_get_assigned_proxies_and_language_code)
    monkeypatch.setattr('handlers.bot', mock_bot)

    await handle_check_proxy(mock_message)

    # Verify that the function retrieves assigned proxies and sends a message
    mock_get_assigned_proxies_and_language_code.assert_called_once_with(1234)
    mock_bot.send_message.assert_called_once_with(1234, '❌ You do not have any assigned proxies. Use /get_proxy to get one.', reply_markup=mock_message.reply_markup)



@pytest.mark.asyncio
async def test_handle_help(monkeypatch):
    """Test the handle_help function."""
    # This test checks if the handle_help function sends
    # the correct help message to the user.
    mock_message = AsyncMock()
    mock_message.chat.id = 1234

    mock_bot = AsyncMock()

    monkeypatch.setattr('handlers.bot', mock_bot)

    await handle_help(mock_message)

    # Verify that the correct help message is sent
    mock_bot.send_message.assert_called_once_with(1234, '📚 Here is a list of available commands:\n🔍 Check Proxy - Check your current proxy.\n🆕 Get Proxy - Get a new random proxy.\n❓ Help - Show this help message.', reply_markup=mock_message.reply_markup)


@pytest.mark.asyncio
async def test_periodic_update(monkeypatch):
    """Test the periodic_update function."""
    # This test verifies that the periodic_update function
    # fetches new proxies and imports them correctly.
    mock_fetch_proxies = AsyncMock(return_value=[{'proxy': 'http://example.com:8080'}])
    mock_import_proxies = AsyncMock()

    monkeypatch.setattr('import_proxies.fetch_proxies', mock_fetch_proxies)
    monkeypatch.setattr('import_proxies.import_proxies', mock_import_proxies)

    try:
        await asyncio.wait_for(periodic_update(), timeout=5.0)  # 5 second timeout
    except asyncio.TimeoutError:
        pass  # We expect periodic_update to run indefinitely, so a timeout is normal

    # Check if proxies are fetched and imported
    mock_fetch_proxies.assert_called_once()
    mock_import_proxies.assert_called_once_with([{'proxy': 'http://example.com:8080'}])



@pytest.mark.asyncio
async def test_handle_start(monkeypatch):
    """Test the handle_start function."""
    # This test checks if the handle_start function sends
    # the correct welcome message and sets up the user.
    mock_message = AsyncMock()
    mock_message.chat.id = 1234
    mock_message.from_user.language_code = 'en'

    mock_bot = AsyncMock()
    mock_assign_proxy = AsyncMock()

    with patch('handlers.bot', new=mock_bot):
        with patch('handlers.assign_proxy', new=mock_assign_proxy):
            await handle_start(mock_message)

    # Verify that welcome messages are sent and user is set up
    assert mock_bot.send_message.call_count == 2
    mock_assign_proxy.assert_called_once_with(1234, None, 'en')


@pytest.mark.asyncio
async def test_handle_main_menu(monkeypatch):
    """Test the handle_main_menu function."""
    # This test verifies that the handle_main_menu function
    # sends the correct menu message to the user.
    mock_message = AsyncMock()
    mock_message.chat.id = 1234

    mock_bot = AsyncMock()

    with patch('handlers.bot', new=mock_bot):
        await handle_main_menu(mock_message)

    # Check if the main menu message is sent
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_path():
    """Test the get_db_path function."""
    # This test checks if the get_db_path function returns
    # the correct path for the database file.
    import os
    db_name = 'proxies'
    expected_path = os.path.join(os.path.dirname(__file__), f'{db_name}.db')
    actual_path = await get_db_path(db_name)
    assert actual_path == expected_path

@pytest.mark.asyncio
async def test_get_assigned_proxies_and_language_code(mock_get_db_path):
    """Test the get_assigned_proxies_and_language_code function."""
    # This test verifies that the function correctly retrieves
    # assigned proxies and language code for a user.
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.side_effect = [('http://example.com:8080', 'en'), None]

    mock_db = AsyncMock()
    mock_db.execute.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor))

    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        assigned_proxies, language_code = await get_assigned_proxies_and_language_code(1234)
        assert assigned_proxies == [{'proxy': 'http://example.com:8080', 'protocol': 'http', 'ip': '127.0.0.1', 'port': 8080, 'country_code': 'US', 'country': 'United States', 'anonymity': 'anonymous', 'https': 'No', 'latency': 100, 'last_checked': 1234567890}]
        assert language_code == 'en'

        assigned_proxies, language_code = await get_assigned_proxies_and_language_code(5678)
        assert assigned_proxies == []
        assert language_code is None

@pytest.mark.asyncio
async def test_assign_proxy(mock_get_db_path):
    """Test the assign_proxy function."""
    # This test checks if the assign_proxy function correctly
    # assigns a new proxy to a user in the database.
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_cursor))

    with patch('aiosqlite.connect', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db), __aexit__=AsyncMock())):
        await assign_proxy(1234, 'http://example.com:8080', 'en')
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()




# Run all tests
if __name__ == '__main__':
    pytest.main()