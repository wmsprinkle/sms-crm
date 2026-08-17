# Deployment Guide

This guide covers deploying the SMS Appointment CRM to production.

## Local Development

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed sample data
python -m scripts.seed

# Start server (DRY_RUN mode, no real SMS)
DRY_RUN=true uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

### Testing CSV Import

```bash
# Import sample leads
curl -F file=@sample-leads.csv \
     -F sequence_id=1 \
     -F 'mapping={"phone":"Phone","first_name":"First"}' \
     http://localhost:8000/imports
```

### Interactive Testing

See `scripts/test_flow.sh` for full end-to-end test:
```bash
bash scripts/test_flow.sh
```

## Docker (Recommended for Production)

### Build & Run

```bash
# Copy template config
cp .env.example .env

# Edit .env with your Telnyx credentials
vim .env

# Build and start
docker compose up --build

# In another terminal, seed the database
docker compose exec app python -m scripts.seed
```

Then:
- CRM console: http://localhost:8000
- API docs: http://localhost:8000/docs

### What's Included

- **Python 3.12-slim** base image
- **FastAPI** application server
- **PostgreSQL** database (production-grade)
- **APScheduler** worker for drip campaigns (starts automatically)

### Network Configuration

If using Docker on a remote server:

1. **Production HTTPS**: Use a reverse proxy (Nginx, Traefik) in front of the app
2. **Telnyx webhook**: Point to your public HTTPS domain, not `localhost`
3. **Environment variables**: Set in `.env` or pass via `-e` flag

Example with environment variables:
```bash
docker run -d \
  -e DATABASE_URL="postgresql://user:pass@db:5432/crm" \
  -e TELNYX_API_KEY="KEY..." \
  -e TELNYX_FROM_NUMBER="+18135550100" \
  -e DRY_RUN="false" \
  -p 8000:8000 \
  wmsprinkle-crm:latest
```

## Cloud Deployment

### AWS (ECS + RDS)

1. **Push Docker image to ECR**:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
   docker tag wmsprinkle-crm:latest <account>.dkr.ecr.<region>.amazonaws.com/wmsprinkle-crm:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/wmsprinkle-crm:latest
   ```

2. **Create RDS Postgres database**:
   - Engine: PostgreSQL 14+
   - Instance: `db.t3.micro` (for small volume)
   - Multi-AZ: optional but recommended

3. **Create ECS task definition**:
   ```json
   {
     "containerDefinitions": [{
       "name": "crm",
       "image": "<ecr-url>:latest",
       "portMappings": [{"containerPort": 8000}],
       "environment": [
         {"name": "DATABASE_URL", "value": "postgresql://..."},
         {"name": "TELNYX_API_KEY", "value": "KEY..."},
         {"name": "DRY_RUN", "value": "false"}
       ],
       "logConfiguration": {
         "logDriver": "awslogs",
         "options": {
           "awslogs-group": "/ecs/wmsprinkle",
           "awslogs-region": "us-east-1",
           "awslogs-stream-prefix": "crm"
         }
       }
     }]
   }
   ```

4. **Create ECS service**:
   - Task definition: above
   - Desired count: 1-2
   - Load balancer: ALB with HTTPS listener
   - VPC security group: allow 443 inbound

5. **Set webhook URL in Telnyx Dashboard**:
   ```
   https://<your-alb-dns>/webhooks/telnyx
   ```

### Heroku

```bash
# Create app
heroku create wmsprinkle-crm

# Add Postgres
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set TELNYX_API_KEY=KEY...
heroku config:set TELNYX_PUBLIC_KEY=...
heroku config:set TELNYX_MESSAGING_PROFILE_ID=...
heroku config:set TELNYX_FROM_NUMBER=+18135550100
heroku config:set DRY_RUN=false

# Deploy
git push heroku main

# Seed database
heroku run python -m scripts.seed
```

### DigitalOcean App Platform

1. Connect GitHub repo
2. Configure build:
   - Dockerfile: auto-detected
3. Configure run:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```
4. Set environment variables in console
5. Add Postgres database via DigitalOcean Managed Databases
6. Deploy

## Self-Hosted (VPS/Dedicated Server)

### Prerequisites

- Ubuntu 22.04+ or similar Linux
- Docker & Docker Compose installed
- Nginx or similar reverse proxy
- SSL certificate (Let's Encrypt, free)

### Setup Steps

1. **Clone repo and enter directory**:
   ```bash
   git clone <repo-url> wmsprinkle
   cd wmsprinkle
   ```

2. **Create `.env` file**:
   ```bash
   cp .env.example .env
   nano .env  # edit with your credentials
   ```

3. **Configure Nginx** (example):
   ```nginx
   server {
     listen 443 ssl http2;
     server_name crm.yourdomain.com;
     
     ssl_certificate /etc/letsencrypt/live/crm.yourdomain.com/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/crm.yourdomain.com/privkey.pem;
     
     location / {
       proxy_pass http://localhost:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto https;
     }
   }
   ```

4. **Start with Docker Compose**:
   ```bash
   docker compose up -d
   docker compose exec app python -m scripts.seed
   ```

5. **Configure Telnyx webhook**:
   ```
   https://crm.yourdomain.com/webhooks/telnyx
   ```

6. **Monitor logs**:
   ```bash
   docker compose logs -f app
   ```

## Database Migrations

For schema changes in production, use Alembic:

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create a migration
alembic revision --autogenerate -m "add contact_tags column"

# Apply migrations
alembic upgrade head
```

See `docs/alembic.md` for details.

## Scaling

### For Higher Volume

1. **Database**: Switch from SQLite to Postgres (already in Docker)
2. **Workers**: Run multiple worker processes:
   ```yaml
   # docker-compose.yml
   app:
     deploy:
       replicas: 3  # or use load balancer
   ```
3. **Telnyx MPS**: Adjust `SEND_RATE_PER_MINUTE` in `.env` (stay within 10DLC limits)
4. **Rate limiting**: Consider adding Redis + rate limiting middleware

### Queue System (Optional)

For thousands of messages/day, add a queue system:

```bash
# Add Redis to docker-compose.yml
docker compose up -d

# Use with APScheduler
```

## Monitoring & Alerts

### Logs

```bash
# Docker logs
docker compose logs -f app

# Persist logs to file
docker compose logs app > logs/app.log
```

### Metrics

The CRM provides `/contacts/metrics` endpoint:
- Total contacts
- Contacts by status
- Messages sent/delivered
- Delivery rate

Use this for dashboards (Grafana, DataDog, etc.):
```bash
curl http://localhost:8000/contacts/metrics
```

### Error Alerts

Set up monitoring for:
- 5xx errors in server logs
- Message failures in Telnyx logs
- Database connection errors
- Worker failures

## Backup & Recovery

### Database Backup

```bash
# With Docker
docker compose exec db pg_dump -U crm crm > backup.sql

# Restore
docker compose exec -T db psql -U crm crm < backup.sql
```

### Recovery

1. Keep backups on S3, Google Cloud Storage, or similar
2. Test restores quarterly
3. Document recovery procedure for your team

## Security Checklist

- [ ] `.env` file is NOT in git (add to .gitignore)
- [ ] API keys rotated quarterly
- [ ] HTTPS enabled on all production endpoints
- [ ] Telnyx webhook signature verification enabled
- [ ] Database password set to strong value
- [ ] Firewall restricts access to admin endpoints if any
- [ ] Regular backups tested
- [ ] Server logs monitored for errors
- [ ] Rate limiting configured for API endpoints

## Troubleshooting

### App won't start
```bash
# Check logs
docker compose logs app

# Check database connection
docker compose exec app python -c "from app.db import engine; engine.connect()"
```

### Webhook not receiving messages
1. Check Telnyx dashboard for webhook status
2. Verify HTTPS certificate is valid
3. Check firewall/security groups allow inbound traffic
4. Verify webhook URL in Telnyx matches deployment

### High message latency
1. Check worker status: `docker compose logs app | grep worker`
2. Check Telnyx queue in dashboard
3. Verify `SEND_RATE_PER_MINUTE` setting
4. Monitor database query times

### Database performance degrading
1. Add indexes (see app/models.py)
2. Archive old messages to separate table
3. Upgrade database instance size

## Support

For Telnyx-specific issues, see `docs/TELNYX_SETUP.md`

For issues with the CRM itself:
1. Check logs: `docker compose logs app`
2. Review error message in console at `/contacts`
3. Check API response: `curl -i http://localhost:8000/contacts/metrics`
