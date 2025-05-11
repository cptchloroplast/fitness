locals {
  root_dir   = abspath("${path.module}/..")
  source_dir = abspath("${local.root_dir}/src/google/")
  output_dir = abspath("${local.root_dir}/tmp/${module.project.project_id}")
}

resource "local_file" "source" {
  for_each = fileset("${local.source_dir}", "**.py")
  filename = "${local.output_dir}/${each.value}"
  source   = "${local.source_dir}/${each.value}"
}

resource "local_file" "requirements" {
  filename = "${local.output_dir}/requirements.txt"
  source   = "${local.root_dir}/requirements.txt"
}

data "archive_file" "default" {
  type        = "zip"
  output_path = "${local.output_dir}.zip"
  source_dir  = local.output_dir

  depends_on = [
    local_file.source,
    local_file.requirements
  ]
}

module "project" {
  source          = "./project"
  name            = var.github_repository
  billing_account = var.google_billing_account
}

module "service_account" {
  source     = "./service_account"
  account_id = var.github_repository
  project    = module.project.project_id
}

module "bucket" {
  source  = "./bucket"
  project = module.project.project_id
  name    = module.project.project_id
  objects = {
    "${module.project.project_id}.zip" = "${local.output_dir}.zip"
  }
}

module "function" {
  source      = "./function"
  project     = module.project.project_id
  entry_point = "run"
  description = "Upload .fit to Garmin"
  environment_variables = {
    GARMIN_TOKEN = var.GARMIN_TOKEN
    SENTRY_DSN   = module.sentry.dsn
  }
  bucket     = module.project.project_id
  object     = "${module.project.project_id}.zip"
  members    = ["serviceAccount:${module.service_account.email}"]
  depends_on = [module.bucket, module.sentry]
}

data "cloudflare_zone" "default" {
  zone_id = var.cloudflare_email_zone_id
}

resource "cloudflare_email_routing_rule" "default" {
  zone_id = var.cloudflare_email_zone_id
  name    = var.github_repository
  enabled = true

  matcher {
    type  = "literal"
    field = "to"
    value = "${var.github_repository}@${data.cloudflare_zone.default.name}"
  }

  action {
    type  = "worker"
    value = [var.github_repository]
  }
}

module "worker" {
  source  = "app.terraform.io/okkema/worker/cloudflare"
  version = "~> 0.6"

  account_id          = var.cloudflare_account_id
  zone_id             = var.cloudflare_zone_id
  name                = var.github_repository
  content             = file("${local.root_dir}/dist/index.js")
  compatibility_flags = ["nodejs_compat_v2"]
  secrets = [
    { name = "SENTRY_DSN", value = module.sentry.dsn },
    { name = "GOOGLE_CREDENTIALS", value = module.service_account.private_key },
  ]
  env_vars = [
    { name = "GOOGLE_FUNCTION_URL", value = module.function.function_uri },
    { name = "WAHOO_EMAIL", value = var.WAHOO_EMAIL },
  ]
}

module "sentry" {
  source  = "app.terraform.io/okkema/project/sentry"
  version = "~> 0.4"

  github_repository   = var.github_repository
  github_organization = "cptchloroplast"
  platform            = "other"
}