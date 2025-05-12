resource "google_project_service" "default" {
  project = var.project
  service = "secretmanager.googleapis.com"
}

resource "google_secret_manager_secret" "default" {
  secret_id = var.secret_id
  project   = var.project

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "default" {
  secret      = google_secret_manager_secret.default.id
  secret_data = var.secret_data
  enabled     = true
}
