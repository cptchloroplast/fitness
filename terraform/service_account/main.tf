resource "google_service_account" "default" {
  account_id  = var.account_id
  project     = var.project
}

resource "google_service_account_key" "default" {
  service_account_id = google_service_account.default.id
}