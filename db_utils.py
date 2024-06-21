import os
import aiosqlite

async def get_db_path(db_name):
    """Get the path to the specified database file."""
    return os.path.join(os.path.dirname(__file__), f'{db_name}.db')

async def init_db():
    """Initialize the database and create the 'proxies' table if it doesn't exist."""
    db_path = await get_db_path('proxies')
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy TEXT NOT NULL,
            status TEXT NOT NULL,
            alive BOOLEAN NOT NULL,
            alive_since REAL,
            anonymity TEXT,
            average_timeout REAL,
            first_seen REAL,
            ip TEXT,
            as_value TEXT,
            asname TEXT,
            city TEXT,
            continent TEXT,
            country TEXT,
            country_code TEXT,
            isp TEXT,
            org TEXT,
            region_name TEXT,
            last_seen REAL,
            port INTEGER,
            protocol TEXT,
            ssl BOOLEAN,
            timeout REAL,
            times_alive INTEGER,
            times_dead INTEGER,
            uptime REAL,
            timezone TEXT,
            zip_code TEXT
        )
        ''')
        await db.commit()


async def get_active_proxy():
    """Get an active proxy from the database."""
    db_path = await get_db_path('proxies')
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT proxy FROM proxies WHERE status = "active" LIMIT 1') as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def replace_proxy(user_id, assigned_proxies):
    """Replace a user's assigned proxy with a new one."""
    db_path = await get_db_path('proxies')
    async with aiosqlite.connect(db_path) as db:
        placeholder = ','.join('?' for _ in assigned_proxies)
        async with db.execute(f'''
        SELECT proxy
        FROM proxies
        WHERE alive = 1 AND proxy NOT IN ({placeholder})
        ORDER BY RANDOM()
        LIMIT 1
        ''', assigned_proxies) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                async with db.execute('SELECT proxy FROM proxies WHERE alive = 1 ORDER BY RANDOM() LIMIT 1') as cursor:
                    result = await cursor.fetchone()
                    return result[0] if result else None

async def create_users_table():
    """Create the 'users' table if it doesn't exist."""
    db_path = await get_db_path('users')
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assigned_proxies TEXT,
            language_code TEXT
        )
        ''')
        await db.commit()

import os
import aiosqlite

# ... (остальной код файла db_utils.py)

async def get_proxy_info(proxy):
    async with aiosqlite.connect(await get_db_path('proxies')) as proxies_db:
        async with proxies_db.execute('SELECT proxy, protocol, ip, port, country_code, country, anonymity, ssl, timeout, last_seen FROM proxies WHERE proxy = ?', (proxy,)) as cursor:
            row = await cursor.fetchone()
            if row:
                proxy, protocol, ip, port, country_code, country, anonymity, ssl, timeout, last_seen = row
                return {
                    'proxy': proxy,
                    'protocol': protocol,
                    'ip': ip,
                    'port': port,
                    'country_code': country_code,
                    'country': country,
                    'anonymity': anonymity,
                    'https': 'Yes' if ssl else 'No',
                    'latency': timeout,
                    'last_checked': last_seen
                }
            else:
                return None

async def get_assigned_proxies_and_language_code(user_id):
    """Get a user's assigned proxies and language code from the database."""
    db_path = await get_db_path('users')
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT assigned_proxies, language_code FROM users WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                assigned_proxies_str = result[0]
                language_code = result[1]
                
                if assigned_proxies_str:
                    async def get_assigned_proxies():
                        proxy_strs = assigned_proxies_str.split(',')
                        for proxy_str in proxy_strs:
                            proxy_info = await get_proxy_info(proxy_str)
                            if proxy_info:
                                yield proxy_info
                    
                    assigned_proxies = [proxy_info async for proxy_info in get_assigned_proxies()]
                else:
                    assigned_proxies = []
                
                return assigned_proxies, language_code
            else:
                return [], None

async def assign_proxy(user_id, new_proxy, language_code):
    """Assign a new proxy to a user."""
    db_path = await get_db_path('users')
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT assigned_proxies FROM users WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()

        if result:
            assigned_proxies = result[0].split(',') if result[0] else []
            if new_proxy and new_proxy not in assigned_proxies:
                if len(assigned_proxies) >= 3:
                    assigned_proxies = assigned_proxies[1:] + [new_proxy]
                else:
                    assigned_proxies.append(new_proxy)
            assigned_proxies_str = ','.join(assigned_proxies)
            await db.execute('UPDATE users SET assigned_proxies = ?, language_code = ? WHERE user_id = ?', (assigned_proxies_str, language_code, user_id))
        else:
            assigned_proxies_str = new_proxy if new_proxy else ''
            await db.execute('INSERT INTO users (user_id, assigned_proxies, language_code) VALUES (?, ?, ?)', (user_id, assigned_proxies_str, language_code))

        await db.commit()