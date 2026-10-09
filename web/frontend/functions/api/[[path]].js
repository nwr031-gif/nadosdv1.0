/**
 * Cloudflare Pages Function: same-origin /api/* proxy.
 *
 * The NADOS FastAPI backend cannot run inside Cloudflare Pages (it is a
 * Python/SQLite process). Deploy it on any HTTP host and set the
 * BACKEND_URL environment variable in the Pages project settings
 * (Settings -> Environment variables). This function then forwards
 * /api/* requests to that backend, so the frontend keeps working with
 * same-origin requests and no CORS configuration.
 *
 * When BACKEND_URL is not configured, a clear 503 JSON error is returned.
 */

export async function onRequest(context) {
  const backend = context.env.BACKEND_URL

  if (!backend) {
    return new Response(
      JSON.stringify({
        detail:
          'NADOS backend is not configured. Set BACKEND_URL in the Cloudflare Pages project settings.',
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      },
    )
  }

  const requestUrl = new URL(context.request.url)
  const targetUrl = backend.replace(/\/+$/, '') + requestUrl.pathname + requestUrl.search

  const proxyHeaders = new Headers(context.request.headers)
  proxyHeaders.delete('host')
  proxyHeaders.delete('cf-connecting-ip')
  proxyHeaders.delete('cf-ray')

  const init = {
    method: context.request.method,
    headers: proxyHeaders,
    redirect: 'follow',
  }

  if (!['GET', 'HEAD'].includes(context.request.method)) {
    init.body = context.request.body
  }

  const upstream = await fetch(targetUrl, init)

  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.delete('content-encoding')
  responseHeaders.delete('content-length')

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  })
}
