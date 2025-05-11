variable "project" {
  description = "Google Cloud project"
  type        = string
}
variable "location" {
  description = "Google Cloud Run function location. Default is \"us-central1\""
  type        = string
  default     = "us-central1"
}
variable "runtime" {
  description = "Google Cloud Run function runtime. Default is \"python311\""
  type        = string
  default     = "python311"
}
variable "entry_point" {
  description = "Google Cloud Run function entry point. Default is \"run\""
  type        = string
  default     = "run"
}
variable "description" {
  description = "Google Cloud Run function description"
  type        = string
}
variable "environment_variables" {
  description = "Google Cloud Run function environment variables"
  type        = map(string)
  default     = null
}
variable "bucket" {
  description = "Google Cloud Storage bucket name"
  type        = string
}
variable "object" {
  description = "Google Cloud Storage object name"
  type        = string
}
variable "members" {
  description = "List of IAM members authorized to invoke the function"
  type        = list(string)
}