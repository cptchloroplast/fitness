import { SentryWorker } from "@okkema/worker/sentry"
import { GoogleFunction } from "@okkema/worker/google"
import { type R2Bucket } from "@cloudflare/workers-types"
import mime from "mime-types"
import { Hono } from "hono"

const KEY = "heatmap.png"

type Environment = {
    SENTRY_DSN: string
    GOOGLE_CREDENTIALS: string
    GOOGLE_FUNCTION_URL_UPLOAD: string
    GOOGLE_FUNCTION_URL_DOWNLOAD: string
    GOOGLE_FUNCTION_URL_HEATMAP: string
    WAHOO_CLIENT_ID: string
    WAHOO_CLIENT_SECRET: string
    WAHOO_WEBHOOK_TOKEN: string
    BACKUP: R2Bucket
}

async function download_activity(env: Environment) {
    console.log("Started downloading workouts from Garmin")
    const downloaded = await GoogleFunction(env.GOOGLE_CREDENTIALS, env.GOOGLE_FUNCTION_URL_DOWNLOAD).fetch({ method: "POST" })
    console.log("Finished downloading workouts from Garmin")
    const status = await downloaded.text()
    console.log(status, downloaded.status)
    if (downloaded.status == 201) {
        console.log("Generating new heatmap")
        const generated = await GoogleFunction(env.GOOGLE_CREDENTIALS, env.GOOGLE_FUNCTION_URL_HEATMAP).fetch({})
        await env.BACKUP.put(KEY, generated.body)
    }
}

const app = new Hono<{ Bindings: Environment }>()
app.get("/", async c => {
    const response = await c.env.BACKUP.get(KEY)
    if (!response) return new Response("Not Found", { status: 404 }) as any
    const buffer = await response.arrayBuffer()
    return new Response(buffer, { headers: { "Content-Type": "image/png" } })
})
app.post("/wahoo", async c => {
    const json = await c.req.json()
    if (json?.webhook_token === c.env.WAHOO_WEBHOOK_TOKEN) 
        throw new Error("Invalid Wahoo webhook token")
    console.log(`Started processing webhook from Wahoo: ${json?.workout_summary?.id}`)
    const link = json?.workout_summary?.file?.url
    if (!link)
        throw new Error("Unable to parse link to .fit download")
    const response = await fetch(link)
    if (!response.ok)
        throw new Error(`Unable to download the .fit file : ${response.status}`)
    const blob = await response.blob()
    const header = response.headers.get("Content-Disposition")
    const name = header?.split(';')?.[1]?.split('=')?.[1]
        ?? `${crypto.randomUUID()}.${mime.extension(blob.type)}`
    const body = new FormData()
    body.append("name", name)
    body.append("file", blob)
    const upload = GoogleFunction(c.env.GOOGLE_CREDENTIALS, c.env.GOOGLE_FUNCTION_URL_UPLOAD)
    const uploaded = await upload.fetch({
        method: "POST",
        body: body as any,
    })
    if (uploaded.ok) {
        const result = await uploaded.json<any>()
        console.log("Uploaded workout to Garmin", result)
    } else {
        const result = await uploaded.text()
        console.log("Failed to upload workout to Garmin", result)
    }
    console.log("Finished processing webhook from Wahoo")
    await download_activity(c.env)
})
app.get("/wahoo/redirect", async c => {
    const code = c.req.query("code")
    if (!code) return c.status(400)
    const url = new URL(c.req.url)
    const body = new URLSearchParams({
        grant_type: "authorization_code",
        redirect_url: url.origin + url.pathname,
        client_id: c.env.WAHOO_CLIENT_ID,
        client_secret: c.env.WAHOO_CLIENT_SECRET,
        code,

    })
    const response = await fetch("https://api.wahooligan.com/oauth/token", {
        method: "POST",
        body,
    })
    if (!response.ok) throw new Error(`Failed to retrieve access token: ${response.status}`)
})

export default SentryWorker<Environment>({
    fetch: app.fetch as any,
    async scheduled(controller, env, ctx) {
        await download_activity(env)
    }
})