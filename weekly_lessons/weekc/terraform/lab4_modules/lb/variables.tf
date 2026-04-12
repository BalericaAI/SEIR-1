variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "instance_group" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "enable_waf" {
  type    = bool
  default = true
}

variable "allowed_ips" {
  type    = list(string)
  default = []
}

