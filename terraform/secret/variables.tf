variable "project" {
  description = "Google project"
  type        = string
}
variable "secret_id" {
  description = "Google Secret id"
  type        = string
}
variable "secret_data" {
  description = "Google Secret data"
  type        = string
  sensitive   = true
}