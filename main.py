import asyncio
import os
import functools
from xml.parsers.expat import ParserCreate

import aiofiles
from aiohttp import ClientSession, log, web
from cairosvg import svg2png as csvg2png


def validate_xml_markup(xml_data : str):
    parser = ParserCreate()
    try:
        parser.Parse(xml_data)
        return True
    except Exception:
        return False

def svg2pngsync(data):
    svgFile = data['svgFile']
    size = data['size']
    csvg2png(url=svgFile, write_to=svgFile.replace('.svg', f'-{size}.png'), output_height=size, output_width=size)

async def svg2png(svgFile, size):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, functools.partial(svg2pngsync, data={'svgFile':svgFile, 'size':size}))

async def monkey(request):
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
    if is_png:
        try:
            size = int(request.rel_url.query['size'])
        except Exception:
            pass
    try:
        if is_png:
            out_name = f'/tmp/monkeyfiles/{address}_optimized-{size}.png'
            await svg2png(f'/tmp/monkeyfiles/{address}_optimized.svg', size)
            return web.FileResponse(out_name)
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
            if is_png:
                out_name = f'/tmp/monkeyfiles/{address}_optimized-{size}.png'
                await svg2png(f'/tmp/monkeyfiles/{address}_optimized.svg', size)
                return web.FileResponse(out_name)
            else:
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