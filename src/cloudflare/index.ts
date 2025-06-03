import PostalMime from "postal-mime"
import { SentryWorker } from "@okkema/worker/sentry"
import { GoogleFunction } from "@okkema/worker/google"
import { type R2Bucket } from "@cloudflare/workers-types"
import mime from "mime-types"

const REGEX = /<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)\1[\S\s]*?download.fit[\S\s]*?<\/a>/

type Environment = {
    SENTRY_DSN: string
    GOOGLE_CREDENTIALS: string
    GOOGLE_FUNCTION_URL: string
    WAHOO_EMAIL: string
    BACKUP: R2Bucket
}

export default SentryWorker<Environment>({
    async email(message, env, ctx) {
        // Validate sender and html body
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
        const client = GoogleFunction(env.GOOGLE_CREDENTIALS, env.GOOGLE_FUNCTION_URL)
        await Promise.all([
            client.fetch({
                method: "POST",
                body: body as any,
            }),
            env.BACKUP.put(name, blob as any),
        ])
    }
})