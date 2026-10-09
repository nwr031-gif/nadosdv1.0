/**
 * NADOS Dv1.0 - Cloudflare Worker (static assets + /api proxy)
 *
 * Serves the built Vue frontend (see [assets] in wrangler.toml) and
 * proxies /api/* to an external NADOS FastAPI backend when the
 * BACKEND_URL variable is configured for this Worker:
 *
 *   npx wrangler secret put BACKEND_URL   # or vars in wrangler.toml
 *
 * The FastAPI backend itself cannot run inside Workers/Pages because it
 * is a Python + SQLite process; host it on any HTTP server and point
 * BACKEND_URL at it (e.g. https://nados-api.example.com).
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
      const backend = env.BACKEND_URL;

      if (!backend) {
        return new Response(
          JSON.stringify({
            detail:
              'NADOS backend is not configured. Set BACKEND_URL for this Worker to the deployed FastAPI server.',
          }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json; charset=utf-8' },
          },
        );
      }

      const target = backend.replace(/\/+$/, '') + url.pathname + url.search;
      const headers = new Headers(request.headers);
      headers.delete('host');

      const init = {
        method: request.method,
        headers,
        redirect: 'follow',
      };
      if (!['GET', 'HEAD'].includes(request.method)) {
        init.body = request.body;
      }

      const upstream = await fetch(target, init);
      const responseHeaders = new Headers(upstream.headers);
      responseHeaders.delete('content-encoding');
      responseHeaders.delete('content-length');

      return new Response(upstream.body, {
        status: upstream.status,
        headers: responseHeaders,
      });
    }

    return env.ASSETS.fetch(request);
  },
};
