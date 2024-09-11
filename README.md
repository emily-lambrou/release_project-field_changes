# Release Changes In GitHub Projects

GitHub doesn't provide a built-in way to send notifications if a field of the project is changing. This
GitHub Action aims to address this by allowing you to identify the change of the release field within a central GitHub project.

## Introduction

This GitHub Action allows you to identify changes in a central GitHub project on opened issues. If the release field changes then  
the assignees of the issue will be informed via comment.


### Prerequisites

Before you can start using this GitHub Action, you'll need to ensure you have the following:

1. A GitHub repository where you want to enable this action.
2. A GitHub project board with custom "Release" field added.
3. "Release" field should be "Single select" type.
5. A Token (Classic) with permissions to repo:*, read:user, user:email, read:project

### Inputs

| Input                                | Description                                                                                      |
|--------------------------------------|--------------------------------------------------------------------------------------------------|
| `gh_token`                           | The GitHub Token                                                                                 |
| `project_number`                     | The project number                                                                               |                                                         
| `release_field_name` _(optional)_    | The release field name. The default is `Release`                                                 |
| `notification_type` _(optional)_     | The notification type. Default is `comment`                                                      |
| `enterprise_github` _(optional)_     | `True` if you are using enterprise github and false if not. Default is `False`                   |
| `repository_owner_type` _(optional)_ | The type of the repository owner (oragnization or user). Default is `user`                       |
| `dry_run` _(optional)_               | `True` if you want to enable dry-run mode. Default is `False`                                    |


### Examples

#### Notify for release change with comment
To set up release change comment notifications, you'll need to create or update a GitHub Actions workflow in your repository. Below is
an example of a workflow YAML file:

```yaml
name: Notify for release change

# Runs every minute
on:
  schedule:
    - cron: '* * * * *'
  workflow_dispatch:

jobs:
  notify_for_release_change:
    runs-on: self-hosted

    steps:
      # Checkout the code to be used by runner
      - name: Checkout code
        uses: actions/checkout@v3

      # Check for release changes
      - name: Check for release changes
        uses: emily-lambrou/release_project-field_changes@v1.3
        with:
          dry_run: ${{ vars.DRY_RUN }}           
          gh_token: ${{ secrets.GH_TOKEN }}      
          project_number: ${{ vars.PROJECT_NUMBER }} 
          enterprise_github: 'True'
          repository_owner_type: organization
        
```

