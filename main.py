import asyncio
import os

import aiofiles
from aiohttp import ClientSession, log, web
from xml.parsers.expat import ParserCreate

def validate_xml_markup(xml_data : str):
    parser = ParserCreate()
    try:
        parser.Parse(xml_data)
        return True
    except Exception:
        return False

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
    await run_command(f'sed -i "s%\'</style>%</style>%g" /tmp/monkeyfiles/{address}.svg')
    await run_command(f'/home/monkey/.cargo/bin/svgcleaner /tmp/monkeyfiles/{address}.svg /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.01)
    # Remove duplicate <svg and </svg
    await run_command(f'sed -i "s%<svg%<g%g" /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.02)
    await run_command(f'sed -i "s%</svg%</g%g" /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.02)
    await run_command(f'sed -i -e "0,/<g/ s/<g/<svg/" /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.02)
    await run_command(f'sed -i "s/....$//" /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.02)
    await run_command(f'echo "</svg>" >> /tmp/monkeyfiles/{address}_optimized.svg')
    await asyncio.sleep(0.02)
    try:
        cached_f = await aiofiles.open(f'/tmp/monkeyfiles/{address}_optimized.svg', mode='r')
        if (validate_xml_markup(await cached_f.read())):
            return web.FileResponse(f'/tmp/monkeyfiles/{address}_optimized.svg')
        else:
            os.remove(f'/tmp/monkeyfiles/{address}_optimized.svg')
            return web.HTTPServerError("something went wrong")
    except Exception:
        return web.HTTPServerError("something went wrong")

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

app = web.Application()
app.router.add_get('/', monkey)
#web.run_app(app, port=9099)