variable "domain" {
  description = "Google Cloud organization domain"
  type        = string
  default     = "okkema.org"
}
variable "name" {
  description = "Project name"
  type        = string
}
variable "prefix" {
  description = "Project prefix. Used to make globally unique identifier"
  default     = "okkema"
  type        = string
}
variable "billing_account" {
  description = "Google Cloud billing account identifier"
  type        = string
}