variable "github_repository" {}
variable "google_billing_account" {}
variable "cloudflare_account_id" {}
variable "cloudflare_zone_id" {}
variable "cloudflare_email_zone_id" {}
variable "GARMIN_TOKEN" {
  sensitive = true
}
variable "WAHOO_CLIENT_ID" {
  sensitive = true
}
variable "WAHOO_CLIENT_SECRET" {
  sensitive = true
}
variable "WAHOO_WEBHOOK_TOKEN" {
  sensitive = true
}
variable "AWS_ACCESS_KEY_ID" {
  sensitive = true
}
variable "AWS_SECRET_ACCESS_KEY" {
  sensitive = true
}
variable "BUCKET_URL" {}