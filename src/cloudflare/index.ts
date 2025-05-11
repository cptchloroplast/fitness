import PostalMime from "postal-mime"
import { SentryWorker } from "@okkema/worker/sentry"
import { GoogleFunction } from "@okkema/worker/google"

const REGEX = /<a\s+(?:[^>]*?\s+)?href=(["'])(.*?)\1[\S\s]*?download.fit[\S\s]*?<\/a>/

type Environment = {
    SENTRY_DSN: string
    GOOGLE_CREDENTIALS: string
    GOOGLE_FUNCTION_URL: string
    WAHOO_EMAIL: string
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
        const get = await fetch(link)
        if (!get.ok)
            throw new Error(`Unable to download the .fit file : ${get.status}`)
        const blob = await get.blob()
        const body = new FormData()
        body.append("file", blob)
        const client = GoogleFunction(env.GOOGLE_CREDENTIALS, env.GOOGLE_FUNCTION_URL)
        await client.fetch({
            method: "POST",
            body: body as any,
        })
    }
})