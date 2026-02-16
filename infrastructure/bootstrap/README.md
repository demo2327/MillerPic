# Terraform Bootstrap (State + Deployer User)

This stack creates:
- S3 bucket for Terraform remote state
- IAM user for Terraform deployment (`millerpic_tf` by default)
- Inline custom policy with required deployment permissions

## Usage

From repository root:

```powershell
Set-Location infrastructure/bootstrap
terraform init
terraform apply -var="bootstrap_profile=pandacloud"
```

If your shell still does not resolve `terraform`, use full path:

```powershell
$terraformPath = "C:\Users\adam\AppData\Local\Microsoft\WinGet\Packages\Hashicorp.Terraform_Microsoft.Winget.Source_8wekyb3d8bbwe\terraform.exe"
Set-Location infrastructure/bootstrap
& $terraformPath init
& $terraformPath apply -var="bootstrap_profile=pandacloud"
```

## After Apply

1. Create access keys for output user (`millerpic_tf` by default).
2. Configure local AWS profile `millerpic_tf` with those keys.
3. Create `infrastructure/backend.tf` using `suggested_backend_block` output from this bootstrap stack.
4. Run Terraform for app infrastructure using the new deployer profile.
