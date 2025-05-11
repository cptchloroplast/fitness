variable "project" {
  type        = string
  description = "Google Cloud project"
}
variable "name" {
  type        = string
  description = "Google Cloud Storage bucket name"
}
variable "objects" {
  description = "Google Cloud Storage objects"
  type        = map(string)
  default     = null
}