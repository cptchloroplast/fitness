resource "google_storage_bucket" "default" {
  name                        = var.name
  project                     = var.project
  location                    = "US"
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "default" {
    for_each = var.objects
    name   = each.key
    bucket = google_storage_bucket.default.name
    source = each.value
}