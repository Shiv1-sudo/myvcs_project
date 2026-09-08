output "environment" {
  description = "Terraform environment."
  value       = local.environment
}

output "kubernetes_context" {
  description = "Kubernetes context used by this environment."
  value       = "docker-desktop"
}