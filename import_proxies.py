import aiosqlite
import aiohttp
import asyncio
import logging
from db_utils import get_db_path, init_db

API_URL = 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=json'
UPDATE_INTERVAL = 300  # 5 minutes

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def import_proxies(data):
    """Import proxies into the database."""
    logging.debug(f"Importing proxies: {data}")
    db_path = await get_db_path('proxies')
    async with aiosqlite.connect(db_path) as db:
        for proxy_data in data:
            proxy = proxy_data['proxy']
            status = 'active'
            alive = proxy_data['alive']
            alive_since = proxy_data.get('alive_since', None)
            anonymity = proxy_data.get('anonymity', None)
            average_timeout = proxy_data.get('average_timeout', None)
            first_seen = proxy_data.get('first_seen', None)
            ip = proxy_data.get('ip', None)
            ip_data = proxy_data.get('ip_data', {})
            as_value = ip_data.get('as', None)
            asname = ip_data.get('asname', None)
            city = ip_data.get('city', None)
            continent = ip_data.get('continent', None)
            country = ip_data.get('country', None)
            country_code = ip_data.get('countryCode', None)
            isp = ip_data.get('isp', None)
            org = ip_data.get('org', None)
            region_name = ip_data.get('regionName', None)
            last_seen = proxy_data.get('last_seen', None)
            port = proxy_data.get('port', None)
            protocol = proxy_data.get('protocol', None)
            ssl = proxy_data.get('ssl', False)
            timeout = proxy_data.get('timeout', None)
            times_alive = proxy_data.get('times_alive', 0)
            times_dead = proxy_data.get('times_dead', 0)
            uptime = proxy_data.get('uptime', None)
            timezone = ip_data.get('timezone', None)
            zip_code = ip_data.get('zip', None)

            try:
                await db.execute('''
                INSERT INTO proxies (proxy, status, alive, alive_since, anonymity, average_timeout, first_seen, ip, as_value, asname, city, continent, country, country_code, isp, org, region_name, last_seen, port, protocol, ssl, timeout, times_alive, times_dead, uptime, timezone, zip_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (proxy, status, alive, alive_since, anonymity, average_timeout, first_seen, ip, as_value, asname, city, continent, country, country_code, isp, org, region_name, last_seen, port, protocol, ssl, timeout, times_alive, times_dead, uptime, timezone, zip_code))
                logging.debug(f"Inserted proxy: {proxy}")
            except Exception as e:
                logging.error(f"Error inserting proxy: {e}")

        try:
            await db.commit()
            logging.info("Proxies imported successfully.")
        except Exception as e:
            await db.rollback()
            logging.error(f"Error committing changes: {e}")

async def fetch_proxies():
    """Fetch proxies from the API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                proxies_data = await response.json()
                logging.info(f"Fetched {len(proxies_data['proxies'])} proxies.")
                logging.debug(f"Proxies data: {proxies_data}")
                return proxies_data['proxies']
            else:
                logging.error(f"Failed to fetch proxies: {response.status}")
                return []

async def periodic_update():
    """Periodically update proxies in the database."""
    while True:
        proxies_data = await fetch_proxies()
        await import_proxies(proxies_data)
        await asyncio.sleep(UPDATE_INTERVAL)

async def main():
    """Main function to initialize the database and start periodic updates."""
    await init_db()
    logging.info("Starting manual update.")
    proxies_data = await fetch_proxies()
    await import_proxies(proxies_data)
    logging.info("Manual update completed.")
    asyncio.create_task(periodic_update())

if __name__ == "__main__":
    asyncio.run(main())