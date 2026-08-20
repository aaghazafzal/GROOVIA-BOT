from aiohttp import web
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

async def handle_request(request):
    return web.Response(text="Groovia Bot is alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logger.info(f"Starting dummy web server on port {port} to satisfy Render.")
    await site.start()
