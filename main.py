import asyncio

import aiofiles
from aiohttp import ClientSession, log, web

async def monkey(request):
    try:
        address = request.rel_url.query['address']
    except KeyError:
        return web.HTTPBadRequest(reason='address parameter is required')
    try:
        cached_f = await aiofiles.open(f'/tmp/monkeyfiles/{address}_optimized.svg', mode='r')
        return web.FileResponse(f'/tmp/monkeyfiles/{address}_optimized.svg')
    except Exception:
        pass
    async with ClientSession() as session:
        url = f"http://bananomonkeys.herokuapp.com/image?address={address}"
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f'/tmp/monkeyfiles/{address}.svg', mode='wb')
                await f.write(await resp.read())
                await f.close()
            else:
                return web.HTTPServerError(reason='monkey API returned error status')
    await run_command(f'/home/monkey/svg_inline_stripper/svgprocess.sh /tmp/monkeyfiles/{address}.svg /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.05)
    return web.FileResponse(f'/tmp/monkeyfiles/{address}_optimized.svg')

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

app = web.Application()
app.router.add_get('/', monkey)
#web.run_app(app, port=9099)