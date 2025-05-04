terraform {
  backend "remote" {
    organization = "okkema"
    workspaces {
      name = "fitness"
    }
  }
  required_providers {
    google = {
      source  = "google"
      version = "~> 6.31"
    }
  }
}