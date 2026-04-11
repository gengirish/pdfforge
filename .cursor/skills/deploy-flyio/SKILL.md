---
name: deploy-flyio
description: Deploy Dockerized backend applications to Fly.io using the flyctl CLI. Use when the user asks to deploy a backend, API server, or Docker container to Fly.io. Covers secrets management, scaling, volumes, health checks, and rollback.
---

# Deploy to Fly.io via CLI

## Prerequisites

- **flyctl CLI**: Install via `curl -L https://fly.io/install.sh | sh` or `brew install flyctl`
- **Authentication**: Run `flyctl auth login`
- **Dockerfile** in project root
- **fly.toml** configuration file

## fly.toml Structure

```toml
app = "your-app-name"
primary_region = "iad"

[build]

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

## Deploy Commands

### First-time launch

```bash
flyctl launch --name your-app-name --region iad --yes
```

### Subsequent deploys

```bash
flyctl deploy --remote-only --app your-app-name
```

The `--remote-only` flag builds the Docker image on Fly.io's remote builders (avoids local Docker requirement).

### Deploy with specific Dockerfile

```bash
flyctl deploy --dockerfile Dockerfile.prod --remote-only
```

## Secrets Management

### Set secrets (triggers redeploy)

```bash
flyctl secrets set SECRET_KEY="value" API_TOKEN="value" --app your-app-name
```

### List secrets

```bash
flyctl secrets list --app your-app-name
```

### Unset a secret

```bash
flyctl secrets unset SECRET_KEY --app your-app-name
```

## Scaling

### Scale memory/CPU

```bash
flyctl scale memory 512 --app your-app-name
flyctl scale count 2 --app your-app-name
```

### Check current scale

```bash
flyctl scale show --app your-app-name
```

## Volumes (for persistent data like SQLite)

```bash
flyctl volumes create data --region iad --size 1 --app your-app-name
```

Mount in `fly.toml`:

```toml
[mounts]
  source = "data"
  destination = "/app/data"
```

## Health Checks

Add to `fly.toml`:

```toml
[[services.http_checks]]
  interval = 10000
  grace_period = "5s"
  method = "get"
  path = "/health"
  protocol = "http"
  timeout = 2000
```

## Monitoring & Logs

```bash
flyctl logs --app your-app-name
flyctl status --app your-app-name
flyctl monitor --app your-app-name
```

## Rollback

```bash
flyctl releases --app your-app-name
flyctl deploy --image registry.fly.io/your-app-name:deployment-XXXXX
```

## Dockerfile Best Practices for Fly.io

- Use non-root user: `RUN addgroup --system app && adduser --system --ingroup app app`
- Create writable directories before switching user: `RUN mkdir -p /app/data && chown app:app /app/data`
- Set `ENV` defaults that match `fly.toml` `[env]` section
- Use gunicorn for Python: `CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--timeout", "120", "--access-logfile", "-"]`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error: no machines in group` | Run `flyctl launch` first to create the app |
| Permission denied on `/data` | Ensure Dockerfile creates dir with correct ownership |
| Deploy succeeds but app crashes | Check `flyctl logs`; verify `CMD` and `PORT` match |
| Secret not taking effect | Secrets trigger rolling redeploy; wait for completion |
| Build timeout | Use `--remote-only` to build on Fly.io builders |

## Post-Deploy Verification

```bash
curl -fsS https://your-app-name.fly.dev/health
curl -fsS https://your-app-name.fly.dev/api/v1/health
```
