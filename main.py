import asyncio

import aiofiles
from aiohttp import ClientSession, log, web

async def monkey(request):
    try:
        address = request.rel_url.query['address']
    except KeyError:
        return web.HTTPBadRequest(reason='address parameter is required')
    async with ClientSession() as session:
        url = f"http://bananomonkeys.herokuapp.com/image?address={address}"
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f'/tmp/monkeyfiles/{address}.svg', mode='wb')
                await f.write(await resp.read())
                await f.close()
            else:
                return web.HTTPServerError(reason='monkey API returned error status')
    await run_command('svgo /tmp/monkeyfiles/'+address+'.svg --enable=inlineStyles --config \'{ "plugins": [ { "inlineStyles": { "onlyMatchedOnce": false } }] }\'')
    return web.FileResponse(f'/tmp/monkeyfiles/{address}.svg')

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

app = web.Application()
app.router.add_get('/', monkey)
#web.run_app(app, port=9099)