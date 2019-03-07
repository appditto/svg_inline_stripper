# SVGCleaner API

Python asyncio web API that runs SVGs through the `svgcleaner` tool. Uses aiofiles and aiohttp.

Middleware for monkeygen.com

Removes and minifies SVGs using [svgcleaner](https://github.com/RazrFalcon/svgcleaner), the main goal is to convert CSS styles to inline styles - but this API wrapper could be modified to use svgo in any way.

# Requirements

Rust is required, to install check: https://www.rust-lang.org/tools/install

```
# virtualenv -p python3.6 venv
# pip install -r requirements.txt
# cargo install svgcleaner
```

# Deployment

See the [aiohttp deployment documentation](https://docs.aiohttp.org/en/stable/deployment.html)