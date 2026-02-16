variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile Terraform should use"
  type        = string
  default     = "millerpic_tf"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "millerpic"
}

variable "s3_bucket_prefix" {
  description = "Prefix used for the photo bucket"
  type        = string
  default     = "millerpic-photos"
}

variable "tags" {
  description = "Default tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "MillerPic"
    ManagedBy = "Terraform"
  }
}
