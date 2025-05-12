terraform {
  backend "remote" {
    organization = "okkema"
    workspaces {
      name = "fitness"
    }
  }
}