locals {
  project_id = "${var.prefix}-${var.name}"
}

data "google_organization" "default" {
  domain = var.domain
}

resource "google_project" "default" {
  name            = var.name
  project_id      = local.project_id
  org_id          = data.google_organization.default.org_id
  deletion_policy = "DELETE"
  billing_account = var.billing_account
}