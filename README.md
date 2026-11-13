# SongVault

SongVault searches Internet Archive audio/video records and offers downloads only when the record metadata indicates Public Domain or Creative Commons licensing.

## Run locally
```bash
docker build -t songvault .
docker run --rm -p 5000:5000 songvault
```
Open http://localhost:5000

## GitHub Actions → ECR → EC2

1. Create an ECR repository named `songvault` in `us-east-2`.
2. Create an EC2 Ubuntu instance with Docker and AWS CLI installed. Attach an EC2 instance role with `AmazonEC2ContainerRegistryReadOnly` so it can pull images.
3. Create an IAM GitHub Actions OIDC provider and role. Trust only your GitHub repo and `refs/heads/main`. Attach permissions to push to the `songvault` ECR repository (`ecr:GetAuthorizationToken` on `*`; and `ecr:BatchCheckLayerAvailability`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:PutImage` on that repository).
4. In GitHub repo Settings → Secrets and variables → Actions, add:
   - `AWS_ROLE_ARN`: IAM role ARN for GitHub Actions
   - `EC2_HOST`: EC2 public IP or DNS
   - `EC2_SSH_KEY`: full private key text (PEM)
5. Ensure EC2 security group allows inbound TCP 22 from your IP and TCP 80 from intended users. Install Docker and AWS CLI on EC2. The SSH user is `ubuntu`.
6. Update `AWS_REGION` in `.github/workflows/deploy.yml` if your ECR/EC2 region differs.
7. Push to `main`; Actions builds the image, pushes it to ECR, then SSH deploys it to EC2.

## Important
- This is not a general-purpose downloader for copyrighted streaming services. It does not bypass DRM, paywalls, or platform restrictions.
- The licensing check is a metadata-based filter, not legal advice or a guarantee. Review the original item’s license/rights page and comply with attribution and share-alike requirements.
- Downloading a source video/audio file does not guarantee it is HD or MP3. This starter app downloads available source media formats; it does not transcode formats.
- For production, replace the demo Flask secret, restrict SSH, pin GitHub Actions to reviewed commit SHAs, add rate limiting and temporary-file cleanup.
