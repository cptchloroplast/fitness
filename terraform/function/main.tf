locals {
  services = [
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com"
  ]
}

data "google_storage_bucket_object" "default" {
  name   = var.object
  bucket = var.bucket
}

resource "google_project_service" "default" {
  for_each = toset(local.services)
  project  = var.project
  service  = each.value
}

resource "google_cloudfunctions2_function" "default" {
  name        = "${var.project}-${var.entry_point}"
  project     = var.project
  location    = var.location
  description = var.description


  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point
    source {
      storage_source {
        bucket     = var.bucket
        object     = var.object
        generation = data.google_storage_bucket_object.default.generation
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 60
    environment_variables = var.environment_variables
  }
}

resource "google_cloud_run_service_iam_member" "default" {
  for_each = toset(var.members)

  location = google_cloudfunctions2_function.default.location
  service  = google_cloudfunctions2_function.default.name
  project  = var.project
  role     = "roles/run.invoker"
  member   = each.value
}
