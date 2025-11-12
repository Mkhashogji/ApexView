# CI/CD Guide - GitLab Pipelines

## Overview

The F1 Engineering App uses GitLab CI/CD for automated testing, building, and containerization. The pipeline ensures code quality and produces deployable Docker images for all services.

## Pipeline Stages

```
lint → test → build → dockerize
```

### Stage 1: Lint

Checks code quality and style compliance.

**Jobs:**
- `lint:web` - ESLint for Next.js frontend
- `lint:api` - Ruff for FastAPI backend
- `lint:ml` - Ruff for ML service

**Duration:** ~30 seconds per job

**Runs On:** All branches and merge requests

### Stage 2: Test

Runs unit tests for all services.

**Jobs:**
- `test:web` - Vitest with coverage
- `test:api` - Pytest for FastAPI
- `test:ml` - Pytest for ML service

**Duration:** ~1-2 minutes per job

**Runs On:** All branches and merge requests

### Stage 3: Build

Compiles production-ready builds.

**Jobs:**
- `build:web` - Next.js production build

**Artifacts:**
- `apps/web/.next/` (expires in 1 week)

**Duration:** ~3-5 minutes

**Runs On:** All branches and merge requests

### Stage 4: Dockerize

Builds and pushes Docker images to GitLab Container Registry.

**Images Produced:**
- `$CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA`
- `$CI_REGISTRY_IMAGE/api:$CI_COMMIT_SHORT_SHA`
- `$CI_REGISTRY_IMAGE/ml:$CI_COMMIT_SHORT_SHA`

**Duration:** ~5-10 minutes (parallel builds)

**Runs On:** All branches (images tagged with commit SHA)

**Main Branch:** Additional `:latest` tags

## GitLab CI/CD Variables

### Required Variables

Set in **Settings → CI/CD → Variables**:

| Variable | Description | Example | Protected | Masked |
|----------|-------------|---------|-----------|--------|
| `CI_REGISTRY_USER` | GitLab username | (auto) | No | No |
| `CI_REGISTRY_PASSWORD` | GitLab token | (auto) | Yes | Yes |
| `CI_REGISTRY` | Registry URL | registry.gitlab.com | No | No |

### Optional Variables

| Variable | Description | Default | When to Set |
|----------|-------------|---------|-------------|
| `LIVE_DATA` | Use live F1 data | `false` | Production |
| `DEFAULT_SEASON` | F1 season | `2025` | Season change |

## Container Registry

### Image Naming Convention

```
registry.gitlab.com/<group>/<project>/web:<tag>
registry.gitlab.com/<group>/<project>/api:<tag>
registry.gitlab.com/<group>/<project>/ml:<tag>
```

**Tags:**
- `<commit-sha>` - Every commit (e.g., `a1b2c3d4`)
- `latest` - Main branch only

### Pulling Images

```bash
# Login to registry
echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER $CI_REGISTRY --password-stdin

# Pull specific version
docker pull registry.gitlab.com/<group>/<project>/web:a1b2c3d4

# Pull latest
docker pull registry.gitlab.com/<group>/<project>/web:latest
```

## Local Pipeline Testing

### Validate .gitlab-ci.yml

```bash
# Install GitLab CI lint tool
pip install gitlab-ci-lint

# Validate syntax
gitlab-ci-lint .gitlab-ci.yml
```

### Run Jobs Locally

Using `gitlab-runner`:

```bash
# Install gitlab-runner
# https://docs.gitlab.com/runner/install/

# Run specific job
gitlab-runner exec docker lint:web

# Run test job
gitlab-runner exec docker test:api
```

## Pipeline Optimization

### Caching

**Node Modules:**
```yaml
cache:
  paths:
    - node_modules/
    - apps/web/node_modules/
```

**Benefits:**
- Faster dependency installation
- Reduced network usage
- Consistent builds

### Parallel Jobs

Lint and test jobs run in parallel across services:

```
lint:web ─┐
lint:api ─┼─→ All lint jobs complete → test stage
lint:ml ──┘
```

### Docker Layer Caching

Dockerfiles are optimized for layer caching:

1. Copy `pyproject.toml` / `package.json` first
2. Install dependencies (cached if unchanged)
3. Copy application code (changes frequently)

## Troubleshooting

### Pipeline Failures

#### Lint Failures

```bash
# Run locally to see errors
pnpm --filter web lint
cd apps/api && ruff check .
cd apps/ml_service && ruff check .

# Auto-fix
pnpm --filter web lint --fix
ruff check --fix .
```

#### Test Failures

```bash
# Run tests locally
pnpm --filter web test
cd apps/api && pytest -v
cd apps/ml_service && pytest -v

# Run with coverage
pytest --cov --cov-report=html
```

#### Docker Build Failures

```bash
# Build locally to debug
docker build -t test-image -f apps/web/Dockerfile .

# Check build context
docker build --progress=plain -t test-image -f apps/web/Dockerfile .

# Validate Dockerfile
docker run --rm -i hadolint/hadolint < apps/web/Dockerfile
```

### Common Issues

#### 1. Docker Login Fails

**Error:** `Error response from daemon: Get https://registry.gitlab.com/v2/: unauthorized`

**Solution:** Check CI/CD variables are set correctly

#### 2. Out of Memory

**Error:** `Killed` during build

**Solution:** Increase GitLab Runner memory or use smaller base images

#### 3. Cache Issues

**Error:** Stale dependencies

**Solution:** Clear pipeline cache in GitLab UI → CI/CD → Pipelines → Clear runner caches

## Best Practices

### Branch Strategy

```
main (protected)
  ├── feature/lap-similarity
  ├── feature/clustering
  └── bugfix/cache-issue
```

**Rules:**
- All branches run full pipeline
- Only `main` produces `:latest` tags
- Merge requests require passing pipeline

### Commit Messages

Follow conventional commits:

```
feat(ml): add lap similarity endpoint
fix(api): resolve parquet cache race condition
docs(readme): update deployment instructions
ci(gitlab): optimize docker builds
```

### Deployment Workflow

1. **Development:** Push to feature branch
2. **Pipeline:** Runs automatically
3. **Review:** Create merge request
4. **Approval:** Pipeline must pass
5. **Merge:** Auto-deploy to staging (future)
6. **Production:** Manual deploy (future)

## Deployment (Future)

### Staging Deployment

```yaml
deploy:staging:
  stage: deploy
  script:
    - kubectl set image deployment/f1-web web=$CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA
  environment:
    name: staging
    url: https://staging.f1-app.example.com
  only:
    - main
```

### Production Deployment

```yaml
deploy:production:
  stage: deploy
  script:
    - kubectl set image deployment/f1-web web=$CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA
  environment:
    name: production
    url: https://f1-app.example.com
  only:
    - main
  when: manual
```

## Monitoring

### Pipeline Metrics

Track in GitLab Analytics:
- Pipeline success rate
- Average duration
- Failure reasons
- Deployment frequency

### Alerts

Set up alerts for:
- ✗ Pipeline failures on `main`
- ✗ Failed deployments
- ⚠️ Slow builds (> 15 minutes)
- ⚠️ Low test coverage (< 70%)

## Security

### Container Scanning

Add security scanning:

```yaml
container_scanning:
  stage: scan
  image: docker:stable
  script:
    - docker run --rm aquasec/trivy image $CI_REGISTRY_IMAGE/web:$CI_COMMIT_SHORT_SHA
```

### Dependency Scanning

```yaml
dependency_scanning:
  stage: test
  script:
    - pip install safety
    - safety check
```

## Cost Optimization

### Tips

1. **Use Pipeline Schedules:** Run full builds nightly, fast builds on push
2. **Limit Dockerize:** Only build images on `main` and release branches
3. **Reduce Test Scope:** Run only affected tests when possible
4. **Use Smaller Images:** Alpine-based images save time and money

### Budget Monitoring

Track CI/CD minutes usage:
- Settings → Usage Quotas → CI/CD minutes
- Set alerts at 80% and 95% usage

## Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitLab Runner](https://docs.gitlab.com/runner/)
- [Container Registry](https://docs.gitlab.com/ee/user/packages/container_registry/)

## Support

For CI/CD issues:
1. Check pipeline logs in GitLab UI
2. Review `.gitlab-ci.yml` syntax
3. Test jobs locally with `gitlab-runner`
4. Consult team leads or DevOps

