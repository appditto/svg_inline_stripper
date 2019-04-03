import asyncio
import os
import functools
import uuid
from xml.parsers.expat import ParserCreate

import aiofiles
from aiohttp import ClientSession, log, web
from cairosvg import svg2png as csvg2png
from PIL import Image
from aioredlock import Aioredlock, LockError

redis_instances = [
  ('localhost', 6379)
]
lock_manager = Aioredlock(redis_instances, lock_timeout = 30, retry_count=10)

def validate_xml_markup(xml_data : str):
    parser = ParserCreate()
    try:
        parser.Parse(xml_data)
        return True
    except Exception:
        return False

def validate_png_sync(path : str):
    try:
        img = Image.load(path)
        img.verify()
        img.close()
        return True
    except Exception:
        return False

async def validate_png(path : str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(validate_png_sync, data={'path':path}))

def svg2pngsync(data):
    svgFile = data['svgFile']
    size = data['size']
    csvg2png(url=svgFile, write_to=svgFile.replace('.svg', f'-{size}.png'), output_height=size, output_width=size)

async def svg2png(svgFile, size):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, functools.partial(svg2pngsync, data={'svgFile':svgFile, 'size':size}))

async def monkey(request):
    rid = uuid.uuid1()
    is_png = False
    size = 1000
    try:
        address = request.rel_url.query['address']
    except KeyError:
        return web.HTTPBadRequest(reason='address parameter is required')
    try:
        if request.rel_url.query['png'] == "true":
            is_png = True
    except KeyError:
        pass
    # Try to acquire a lock
    try:
        async with await lock_manager.lock(address) as lock:
            if is_png:
                try:
                    size = int(request.rel_url.query['size'])
                except Exception:
                    pass
            try:
                if is_png:
                    out_name = f'/tmp/monkeyfiles/static/{address}_optimized-{size}.png'
                    try:
                        cached_f = await aiofiles.open(out_name, mode='r')
                        if not await validate_png(out_name):
                          raise Exception
                        return web.HTTPFound(f'https://monkeys.appditto.com/static/{address}_optimized-{size}.png')
                    except Exception:
                        pass
                    await svg2png(f'/tmp/monkeyfiles/static/{address}_optimized.svg', size)
                    return web.HTTPFound(f'https://monkeys.appditto.com/static/{address}_optimized-{size}.png')
                cached_f = await aiofiles.open(f'/tmp/monkeyfiles/static/{address}_optimized.svg', mode='r')
                return web.HTTPFound(f'https://monkeys.appditto.com/static/{address}_optimized.svg')
            except Exception:
                pass
            async with ClientSession() as session:
                url = f"http://bananomonkeys.herokuapp.com/image?address={address}"
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 200:
                        f = await aiofiles.open(f'/tmp/monkeyfiles/static/{rid}.svg', mode='wb')
                        await f.write(await resp.read())
                        await f.close()
                    else:
                        return web.HTTPInternalServerError(reason='monkey API returned error status')
            await run_command(f'sed -i "s%\'</style>%</style>%g" /tmp/monkeyfiles/static/{rid}.svg')
            await run_command(f'/home/monkey/.cargo/bin/svgcleaner /tmp/monkeyfiles/static/{rid}.svg /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.01)
            # Remove duplicate <svg and </svg
            await run_command(f'sed -i "s%<svg%<g%g" /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.02)
            await run_command(f'sed -i "s%</svg%</g%g" /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.02)
            await run_command(f'sed -i -e "0,/<g/ s/<g/<svg/" /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.02)
            await run_command(f'sed -i "s/....$//" /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.02)
            await run_command(f'echo "</svg>" >> /tmp/monkeyfiles/static/{address}_optimized.svg')
            await asyncio.sleep(0.02)
            try:
                cached_f = await aiofiles.open(f'/tmp/monkeyfiles/static/{address}_optimized.svg', mode='r')
                if (validate_xml_markup(await cached_f.read())):
                    if is_png:
                        out_name = f'/tmp/monkeyfiles/static/{address}_optimized-{size}.png'
                        await svg2png(f'/tmp/monkeyfiles/static/{address}_optimized.svg', size)
                        return web.HTTPFound(f'https://monkeys.appditto.com/static/{address}_optimized-{size}.png')
                    else:
                        return web.HTTPFound(f'https://monkeys.appditto.com/static/{address}_optimized.svg')
                else:
                    os.remove(f'/tmp/monkeyfiles/static/{address}_optimized.svg')
                    return web.HTTPInternalServerError(reason="something went wrong")
            except Exception:
                return web.HTTPInternalServerError(reason="something went wrong")
    except LockError:
        return web.HTTPInternalServerError(reason="something went wrong")

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

app = web.Application()
app.router.add_get('/', monkey)
#web.run_app(app, port=9099)
