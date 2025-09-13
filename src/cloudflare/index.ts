import PostalMime from "postal-mime"
import { SentryWorker } from "@okkema/worker/sentry"
import { GoogleFunction } from "@okkema/worker/google"
import { ExecutionContext, type R2Bucket } from "@cloudflare/workers-types"
import mime from "mime-types"

const REGEX = /<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)\1[\S\s]*?download.fit[\S\s]*?<\/a>/
const KEY = "heatmap.png"

type Environment = {
    SENTRY_DSN: string
    GOOGLE_CREDENTIALS: string
    GOOGLE_FUNCTION_URL_UPLOAD: string
    GOOGLE_FUNCTION_URL_DOWNLOAD: string
    GOOGLE_FUNCTION_URL_HEATMAP: string
    WAHOO_EMAIL: string
    BACKUP: R2Bucket
}

async function download_activity(env: Environment, ctx: ExecutionContext) {
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

export default SentryWorker<Environment>({
    async fetch(request, env, ctx) {
        const response = await env.BACKUP.get(KEY)
        if (!response) return new Response("Not Found", { status: 404 }) as any
        const buffer = await response.arrayBuffer()
        return new Response(buffer, { headers: { "Content-Type": "image/png"}})
    },
    async email(message, env, ctx) {
        console.log("Started processing email from Wahoo")
        const email = await PostalMime.parse(message.raw)
        if (email.from.address != env.WAHOO_EMAIL)
            throw new Error(`Unkown sender: ${email.from.address}`)
        if (!email.html)
            throw new Error("Unable to view email HTML")
        const link = email.html.match(REGEX)?.[2]
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
        const upload = GoogleFunction(env.GOOGLE_CREDENTIALS, env.GOOGLE_FUNCTION_URL_UPLOAD)
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
        console.log("Finished processing email from Wahoo")
        await download_activity(env, ctx)
    },
    async scheduled(controller, env, ctx) {
        await download_activity(env, ctx)
    }
})