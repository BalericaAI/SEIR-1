terraform {
  backend "gcs" {
    bucket  = "backendformytf"
    prefix  = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}
