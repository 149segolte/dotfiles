resource "terraform_data" "example" {
  input = "fake-string"

  lifecycle {
    action_trigger {
      events  = [before_create]
      actions = [action.homelab_example.example]
    }
  }
}

action "homelab_example" "example" {
  config {
    configurable_attribute = "some-value"
  }
}
