terraform {
  backend "s3" {
    bucket  = "millerpic-terraform-state-926350377840-us-east-1"
    key     = "millerpic/us-east-1/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
    profile = "millerpic_tf"
  }
}
