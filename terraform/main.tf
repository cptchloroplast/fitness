locals {
  root_dir   = abspath("${path.module}/..")
  source_dir = abspath("${local.root_dir}/src/google/")
  output_dir = abspath("${local.root_dir}/tmp/${module.project.project_id}")
  secrets = {
    "garmin-token" : var.GARMIN_TOKEN
    "aws-access-key-id" : var.AWS_ACCESS_KEY_ID
    "aws-secret-access-key" : var.AWS_SECRET_ACCESS_KEY
  }
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
  source  = "app.terraform.io/okkema/project/google"
  version = "~> 0.1"

  name            = var.github_repository
  billing_account = var.google_billing_account
}

module "service_account" {
  source  = "app.terraform.io/okkema/service_account/google"
  version = "~> 0.1"

  account_id = var.github_repository
  project    = module.project.project_id
}

module "bucket" {
  source  = "app.terraform.io/okkema/bucket/google"
  version = "~> 0.1"

  project = module.project.project_id
  name    = module.project.project_id
  objects = {
    "${module.project.project_id}.zip" = "${local.output_dir}.zip"
  }
}

module "secret" {
  source   = "app.terraform.io/okkema/secret/google"
  version  = "~> 0.1"
  for_each = local.secrets

  project     = module.project.project_id
  secret_id   = each.key
  secret_data = each.value
}

module "upload" {
  source  = "app.terraform.io/okkema/function/google"
  version = "~> 0.2"

  project     = module.project.project_id
  entry_point = "garmin_upload"
  description = "Upload .fit file to Garmin"
  environment_variables = {
    SENTRY_DSN = module.sentry.dsn
  }
  secrets = {
    GARMIN_TOKEN = "garmin-token"
  }
  bucket     = module.project.project_id
  object     = "${module.project.project_id}.zip"
  members    = ["serviceAccount:${module.service_account.email}"]
  depends_on = [module.bucket, module.sentry]
}

module "download" {
  source  = "app.terraform.io/okkema/function/google"
  version = "~> 0.2"

  project     = module.project.project_id
  entry_point = "garmin_download"
  description = "Download Garmin activities to bucket"
  available_cpu    = 1
  available_memory = "2Gi"
  timeout_seconds  = 300
  environment_variables = {
    SENTRY_DSN = module.sentry.dsn
    BUCKET_URL = var.BUCKET_URL
  }
  secrets = {
    GARMIN_TOKEN          = "garmin-token"
    AWS_ACCESS_KEY_ID     = "aws-access-key-id"
    AWS_SECRET_ACCESS_KEY = "aws-secret-access-key"
  }
  bucket     = module.project.project_id
  object     = "${module.project.project_id}.zip"
  members    = ["serviceAccount:${module.service_account.email}"]
  depends_on = [module.bucket, module.sentry]
}

module "heatmap" {
  source  = "app.terraform.io/okkema/function/google"
  version = "~> 0.2"

  project          = module.project.project_id
  entry_point      = "generate_heatmap"
  description      = "Generate heatmap from activities"
  available_cpu    = 1
  available_memory = "2Gi"
  timeout_seconds  = 300
  environment_variables = {
    SENTRY_DSN = module.sentry.dsn
    BUCKET_URL = var.BUCKET_URL
  }
  secrets = {
    AWS_ACCESS_KEY_ID     = "aws-access-key-id"
    AWS_SECRET_ACCESS_KEY = "aws-secret-access-key"
  }
  bucket     = module.project.project_id
  object     = "${module.project.project_id}.zip"
  members    = ["serviceAccount:${module.service_account.email}"]
  depends_on = [module.bucket, module.sentry]
}

module "email_rule" {
  source  = "app.terraform.io/okkema/email_rule/cloudflare"
  version = "~> 0.1"

  zone_id = var.cloudflare_email_zone_id
  name    = var.github_repository
  worker  = var.github_repository
}

module "worker" {
  source  = "app.terraform.io/okkema/worker/cloudflare"
  version = "~> 0.6"

  account_id          = var.cloudflare_account_id
  zone_id             = var.cloudflare_zone_id
  name                = var.github_repository
  content             = file("${local.root_dir}/dist/index.js")
  hostnames           = [var.github_repository]
  compatibility_flags = ["nodejs_compat_v2"]
  schedules           = ["0 0 * * *"]
  secrets = [
    { name = "SENTRY_DSN", value = module.sentry.dsn },
    { name = "GOOGLE_CREDENTIALS", value = module.service_account.private_key },
  ]
  env_vars = [
    { name = "GOOGLE_FUNCTION_URL_UPLOAD", value = module.upload.function_uri },
    { name = "GOOGLE_FUNCTION_URL_DOWNLOAD", value = module.download.function_uri },
    { name = "GOOGLE_FUNCTION_URL_HEATMAP", value = module.heatmap.function_uri },
    { name = "WAHOO_EMAIL", value = var.WAHOO_EMAIL },
  ]
  buckets = [
    { name = var.github_repository, binding = "BACKUP" }
  ]
}

module "sentry" {
  source  = "app.terraform.io/okkema/project/sentry"
  version = "~> 0.4"

  github_repository   = var.github_repository
  github_organization = "cptchloroplast"
  platform            = "other"
}

module "backup" {
  source  = "app.terraform.io/okkema/bucket/cloudflare"
  version = "~> 1.0"

  account_id = var.cloudflare_account_id
  name       = var.github_repository
}
