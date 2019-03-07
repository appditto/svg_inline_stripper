# SVGO API

Python asyncio web API that runs SVGs through the `svgo` tool. Uses aiofiles and aiohttp.

Middleware for monkeygen.com

Removes and minifies SVGs using [SVGO](https://github.com/svg/svgo), the main goal is to convert CSS styles to inline styles - but this API wrapper could be modified to use svgo in any way.

# Requirements

Recommended setup (NodeJS is required also for SVGO):

```
# virtualenv -p python3.6 venv
# pip install -r requirements.txt
# npm install -g svgo
```

# Deployment

See the [aiohttp deployment documentation](https://docs.aiohttp.org/en/stable/deployment.html)