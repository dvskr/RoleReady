# RoleReady Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- SSL certificates (for HTTPS)
- Domain name configured
- Environment variables configured

### 1. Environment Setup
```bash
# Copy environment template
cp .env.production.example .env.production

# Edit with your production values
nano .env.production
```

### 2. SSL Certificates
```bash
# Create SSL directory
mkdir ssl

# Place your SSL certificates
# cert.pem -> ssl/cert.pem
# key.pem -> ssl/key.pem
```

### 3. Deploy
```bash
# Run deployment script
./scripts/deploy.sh
```

## 📋 Production Checklist

### ✅ Security
- [ ] SSL certificates configured
- [ ] Environment variables secured
- [ ] Database passwords are strong
- [ ] API keys are production keys
- [ ] Security headers enabled
- [ ] Rate limiting configured

### ✅ Performance
- [ ] Docker images optimized
- [ ] Gzip compression enabled
- [ ] Static file caching configured
- [ ] Database connection pooling
- [ ] Redis caching enabled
- [ ] CDN configured (optional)

### ✅ Monitoring
- [ ] Health checks configured
- [ ] Logging setup
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Database monitoring

### ✅ Backup & Recovery
- [ ] Database backups scheduled
- [ ] File storage backups
- [ ] Disaster recovery plan
- [ ] Rollback procedures

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `APP_URL` | Production domain | ✅ |
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `REDIS_PASSWORD` | Redis password | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | ✅ |
| `SUPABASE_URL` | Supabase URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service key | ✅ |
| `JWT_SECRET` | JWT signing secret | ✅ |
| `ENCRYPTION_KEY` | Data encryption key | ✅ |

### Docker Services
- **postgres**: Database server
- **redis**: Caching layer
- **api**: FastAPI backend
- **web**: Next.js frontend
- **nginx**: Reverse proxy

## 🏥 Health Checks

### Manual Health Check
```bash
# Run health check script
./scripts/health-check.sh
```

### API Health
```bash
curl https://your-domain.com/api/health
```

### Web Health
```bash
curl https://your-domain.com
```

## 📊 Monitoring

### Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f web
```

### Service Status
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run health checks
./scripts/health-check.sh
```

### Database Migrations
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api python -m alembic upgrade head
```

### Backup Database
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U roleready roleready > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U roleready roleready < backup.sql
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check environment variables
docker-compose -f docker-compose.prod.yml config
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U roleready

# Test connection
docker-compose -f docker-compose.prod.yml exec api python -c "
from roleready_api.core.supabase import supabase_client
print('Database connected:', supabase_client.table('users').select('*').limit(1).execute())
"
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Test SSL
openssl s_client -connect your-domain.com:443
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# In docker-compose.prod.yml
api:
  deploy:
    replicas: 3

web:
  deploy:
    replicas: 2
```

### Load Balancing
- Use nginx upstream configuration
- Configure health checks
- Set up sticky sessions if needed

## 🔒 Security Best Practices

1. **Regular Updates**: Keep Docker images and dependencies updated
2. **Access Control**: Use strong passwords and API keys
3. **Network Security**: Configure firewalls and VPNs
4. **Monitoring**: Set up intrusion detection
5. **Backup**: Regular automated backups
6. **Logging**: Monitor access and error logs

## 📞 Support

For production issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Run health checks: `./scripts/health-check.sh`
3. Check service status: `docker-compose -f docker-compose.prod.yml ps`
4. Review this documentation
5. Contact support team
