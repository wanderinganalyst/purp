# Deployment Guide

This directory contains deployment configurations and guides for various platforms.

## Quick Links

- [AWS Deployment](aws.md) - Production deployment to Amazon Web Services
- [Docker Deployment](docker.md) - Containerized deployment with Docker Compose

## Deployment Options

### AWS (Recommended for Production)

**Infrastructure:**
- EC2 instance for application server
- RDS PostgreSQL for database
- Nginx reverse proxy
- Automated deployment scripts

**Cost:** ~$34/month for small production setup

**Best for:**
- Production deployments
- Scalable infrastructure
- Managed database backups
- High availability needs

[Full AWS Guide →](aws.md)

### Docker

**Infrastructure:**
- Docker containers for app and database
- Docker Compose orchestration
- Volume mounts for data persistence

**Cost:** Free (self-hosted)

**Best for:**
- Local development
- Testing environments
- Self-hosted deployments
- Container-based infrastructure

[Full Docker Guide →](docker.md)

## Choosing a Deployment Method

| Feature | AWS | Docker |
|---------|-----|--------|
| Production-ready | ✅ Yes | ⚠️ Depends |
| Managed database | ✅ RDS | ❌ Self-managed |
| Auto-scaling | ✅ Yes | ❌ Manual |
| SSL/HTTPS | ✅ Easy (Certbot) | ⚠️ Manual |
| Cost | ~$34/month | Free (hosting costs) |
| Complexity | Medium | Low |
| Backups | ✅ Automated | ⚠️ Manual |

## Prerequisites

All deployment methods require:
- Git repository access
- Environment variables configured
- Database credentials
- Flask SECRET_KEY

## Support

- **Documentation Issues**: Open GitHub issue
- **AWS Support**: AWS Support Console
- **Docker Support**: Docker community forums
