# Infrastructure Architecture Diagrams

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Developer                             │
│                                                              │
│  Runs: ./deploy.sh                                          │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ Selects Cloud & Environment
                │
                ▼
┌───────────────────────────────────────────────────────────────┐
│                     Deployment Script                         │
│                                                               │
│  1. Check Prerequisites (Terraform, Ansible, jq)             │
│  2. Verify Cloud Credentials                                 │
│  3. Run Terraform                                             │
│  4. Wait for Instance                                         │
│  5. Run Ansible                                               │
└───────┬───────────────────────────────┬──────────────────────┘
        │                               │
        │ Terraform                     │ Ansible
        ▼                               ▼
┌─────────────────┐           ┌────────────────────────┐
│  Infrastructure │           │  Application Deployment │
│  Provisioning   │           │                        │
│                 │           │  - Install packages    │
│  - VPC/Network  │           │  - Setup Docker        │
│  - Security     │           │  - Copy app files      │
│  - Compute      │           │  - Create venv         │
│  - SSH Keys     │           │  - Install deps        │
│  - Public IP    │           │  - Configure systemd   │
└────────┬────────┘           │  - Setup nginx         │
         │                    └────────┬───────────────┘
         │                             │
         └──────────┬──────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │    Cloud Infrastructure    │
        │                           │
        │  ┌─────────────────────┐ │
        │  │   Nginx (Port 80)   │ │
        │  │         ▼           │ │
        │  │  Gunicorn (5000)    │ │
        │  │         ▼           │ │
        │  │   Flask App         │ │
        │  │         ▼           │ │
        │  │  SQLite Database    │ │
        │  └─────────────────────┘ │
        │                           │
        │  Ubuntu 22.04 Instance    │
        └───────────────────────────┘
```

## AWS Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │             VPC (10.0.0.0/16)                         │  │
│  │                                                       │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  Public Subnet (10.0.1.0/24)                 │    │  │
│  │  │                                               │    │  │
│  │  │  ┌────────────────────────────────────┐      │    │  │
│  │  │  │  EC2 Instance                      │      │    │  │
│  │  │  │  - Ubuntu 22.04                    │      │    │  │
│  │  │  │  - Production: t3.medium           │      │    │  │
│  │  │  │  - Demo: t3.micro                  │      │    │  │
│  │  │  │                                     │      │    │  │
│  │  │  │  ┌──────────────────────────┐      │      │    │  │
│  │  │  │  │  Application Stack       │      │      │    │  │
│  │  │  │  │  - Nginx (:80)           │◄─────┼──────┼────┼──── Internet
│  │  │  │  │  - Gunicorn (:5000)      │      │      │    │  │
│  │  │  │  │  - Flask App             │      │      │    │  │
│  │  │  │  │  - SQLite DB             │      │      │    │  │
│  │  │  │  └──────────────────────────┘      │      │    │  │
│  │  │  └────────────────────────────────────┘      │    │  │
│  │  │                                               │    │  │
│  │  └───────────────────────┬───────────────────────┘    │  │
│  │                          │                            │  │
│  │  ┌───────────────────────▼────────────────────┐      │  │
│  │  │  Security Group                            │      │  │
│  │  │  - SSH (22)        ✓                       │      │  │
│  │  │  - HTTP (80)       ✓                       │      │  │
│  │  │  - HTTPS (443)     ✓                       │      │  │
│  │  │  - App Port (5000) ✓                       │      │  │
│  │  └────────────────────────────────────────────┘      │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────┐      │  │
│  │  │  Internet Gateway                          │      │  │
│  │  └────────────────────────────────────────────┘      │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  SSH Key Pair (Auto-generated RSA 4096)              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Azure Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Azure Cloud                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        Resource Group                                  │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  Virtual Network (10.0.0.0/16)               │     │  │
│  │  │                                               │     │  │
│  │  │  ┌────────────────────────────────────┐      │     │  │
│  │  │  │  Subnet (10.0.1.0/24)              │      │     │  │
│  │  │  │                                     │      │     │  │
│  │  │  │  ┌──────────────────────────┐      │      │     │  │
│  │  │  │  │  Linux VM                │      │      │     │  │
│  │  │  │  │  - Ubuntu 22.04          │      │      │     │  │
│  │  │  │  │  - Prod: Standard_B2s    │      │      │     │  │
│  │  │  │  │  - Demo: Standard_B1s    │      │      │     │  │
│  │  │  │  │                           │      │      │     │  │
│  │  │  │  │  Application Stack        │◄─────┼──────┼─────┼─── Internet
│  │  │  │  │  - Nginx (:80)            │      │      │     │  │
│  │  │  │  │  - Gunicorn (:5000)       │      │      │     │  │
│  │  │  │  │  - Flask App              │      │      │     │  │
│  │  │  │  └──────────────────────────┘      │      │     │  │
│  │  │  │                                     │      │     │  │
│  │  │  │  ┌──────────────────────────┐      │      │     │  │
│  │  │  │  │  Network Interface        │      │      │     │  │
│  │  │  │  └──────────────────────────┘      │      │     │  │
│  │  │  └────────────────────────────────────┘      │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  Public IP Address (Static)                  │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  Network Security Group                      │     │  │
│  │  │  - SSH (22)        ✓                         │     │  │
│  │  │  - HTTP (80)       ✓                         │     │  │
│  │  │  - HTTPS (443)     ✓                         │     │  │
│  │  │  - App Port (5000) ✓                         │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## GCP Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      GCP Cloud                                │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        Project                                         │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  VPC Network (Custom)                        │     │  │
│  │  │                                               │     │  │
│  │  │  ┌────────────────────────────────────┐      │     │  │
│  │  │  │  Subnet (10.0.1.0/24)              │      │     │  │
│  │  │  │                                     │      │     │  │
│  │  │  │  ┌──────────────────────────┐      │      │     │  │
│  │  │  │  │  Compute Instance        │      │      │     │  │
│  │  │  │  │  - Ubuntu 22.04          │      │      │     │  │
│  │  │  │  │  - Prod: e2-medium       │      │      │     │  │
│  │  │  │  │  - Demo: e2-micro        │      │      │     │  │
│  │  │  │  │                           │      │      │     │  │
│  │  │  │  │  Application Stack        │◄─────┼──────┼─────┼─── Internet
│  │  │  │  │  - Nginx (:80)            │      │      │     │  │
│  │  │  │  │  - Gunicorn (:5000)       │      │      │     │  │
│  │  │  │  │  - Flask App              │      │      │     │  │
│  │  │  │  └──────────────────────────┘      │      │     │  │
│  │  │  │                                     │      │     │  │
│  │  │  │  ┌──────────────────────────┐      │      │     │  │
│  │  │  │  │  External IP (Ephemeral) │      │      │     │  │
│  │  │  │  └──────────────────────────┘      │      │     │  │
│  │  │  └────────────────────────────────────┘      │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  Firewall Rules                              │     │  │
│  │  │  - fw-ssh (22)       ✓                       │     │  │
│  │  │  - fw-http (80)      ✓                       │     │  │
│  │  │  - fw-https (443)    ✓                       │     │  │
│  │  │  - fw-app (5000)     ✓                       │     │  │
│  │  │  Target Tags: [app-production/demo]          │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Deployment Flow

```
┌──────────┐
│  Start   │
└────┬─────┘
     │
     ▼
┌────────────────────┐
│ Check Prerequisites│
│ - Terraform        │
│ - Ansible          │
│ - jq               │
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Select Cloud       │
│ 1. AWS             │
│ 2. Azure           │───────────┐
│ 3. GCP             │           │
└────┬───────────────┘           │
     │                           │
     ▼                           ▼
┌────────────────────┐    ┌──────────────┐
│ Select Environment │    │ GCP Project? │
│ 1. Production      │    │ (if GCP)     │
│ 2. Demo            │    └──────────────┘
└────┬───────────────┘           │
     │                           │
     ▼◄──────────────────────────┘
┌────────────────────┐
│ Verify Credentials │
│ - AWS: Check keys  │
│ - Azure: Check az  │
│ - GCP: Check gcloud│
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Terraform Init     │
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Terraform Plan     │
│ - VPC/Network      │
│ - Security         │
│ - Compute          │
│ - SSH Keys         │
└────┬───────────────┘
     │
     ▼
┌────────────────────┐
│ Confirm Apply?     │◄───── NO ──┐
└────┬───────────────┘            │
     │ YES                        │
     ▼                            │
┌────────────────────┐            │
│ Terraform Apply    │            │
│ - Create Resources │            │
│ - Generate Keys    │            │
│ - Save Outputs     │            │
└────┬───────────────┘            │
     │                            │
     ▼                            │
┌────────────────────┐            │
│ Wait for SSH       │            │
│ - Max 30 attempts  │            │
│ - 10s between      │            │
└────┬───────────────┘            │
     │                            │
     ▼                            │
┌────────────────────┐            │
│ Ansible Deploy     │            │
│ - Install packages │            │
│ - Setup Docker     │            │
│ - Copy app files   │            │
│ - Create venv      │            │
│ - Install deps     │            │
│ - Configure systemd│            │
│ - Setup Nginx      │            │
└────┬───────────────┘            │
     │                            │
     ▼                            │
┌────────────────────┐            │
│ Display Info       │            │
│ - IP Address       │            │
│ - URL              │            │
│ - SSH Command      │            │
│ - Destroy Info     │            │
└────┬───────────────┘            │
     │                            │
     ▼                            │
┌────────────────────┐            │
│   Success!         │            │
└────────────────────┘            │
                                  │
                           ┌──────┴──────┐
                           │   Cancel    │
                           └─────────────┘
```

## File Structure

```
infrastructure/
│
├── terraform/                      # Infrastructure provisioning
│   ├── main.tf                     # Main orchestration
│   ├── modules/
│   │   ├── aws/
│   │   │   └── main.tf             # AWS resources
│   │   ├── azure/
│   │   │   └── main.tf             # Azure resources
│   │   └── gcp/
│   │       └── main.tf             # GCP resources
│   └── environments/
│       ├── production.tfvars       # Production config
│       └── demo.tfvars             # Demo config
│
├── ansible/                        # Application deployment
│   ├── playbooks/
│   │   ├── deploy-app.yml          # Main playbook
│   │   └── templates/
│   │       ├── env.j2              # Environment vars
│   │       ├── becauseimstuck.service.j2  # Systemd
│   │       └── nginx.conf.j2       # Nginx config
│   └── requirements.txt            # Ansible dependencies
│
├── scripts/                        # Automation
│   ├── deploy.sh                   # Deploy everything
│   └── destroy.sh                  # Destroy infrastructure
│
├── keys/                           # SSH keys (auto-generated)
│   └── .gitignore                  # Don't commit keys
│
├── README.md                       # Full documentation
├── QUICKSTART.md                   # Quick start guide
├── SUMMARY.md                      # What was created
├── ARCHITECTURE.md                 # This file
├── Makefile                        # Convenience commands
└── .gitignore                      # Git ignore rules
```

## Component Communication

```
┌──────────────┐     SSH      ┌──────────────┐
│  Developer   │─────────────►│   Instance   │
│  (Local)     │              │  (Cloud)     │
└──────┬───────┘              └──────┬───────┘
       │                             │
       │ Terraform                   │
       │ (Provision)                 │
       ▼                             │
┌──────────────┐                     │
│  Cloud API   │                     │
│  - AWS       │                     │
│  - Azure     │                     │
│  - GCP       │                     │
└──────┬───────┘                     │
       │                             │
       │ Creates                     │
       ▼                             │
┌──────────────┐                     │
│  Resources   │                     │
│  - Network   │                     │
│  - Compute   │                     │
│  - Security  │                     │
└──────────────┘                     │
                                     │
       ┌─────────────────────────────┘
       │ Ansible
       │ (Configure)
       ▼
┌──────────────┐
│  App Stack   │
│  - Nginx     │──► Port 80 ──► Internet
│  - Gunicorn  │
│  - Flask     │
│  - SQLite    │
└──────────────┘
```

## Network Flow

```
Internet Request
       │
       ▼
┌──────────────────┐
│  Public IP       │
│  (Cloud Provider)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Firewall/NSG    │
│  Port 80 ✓       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Nginx           │
│  Reverse Proxy   │
│  :80 -> :5000    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Gunicorn        │
│  WSGI Server     │
│  4 Workers       │
│  Port 5000       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Flask App       │
│  Python 3.10     │
│  Virtual Env     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  SQLite DB       │
│  instance/       │
└──────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────┐
│  Layer 1: Cloud Firewall            │
│  - Only specified ports allowed     │
│  - Source IP filtering possible     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Layer 2: SSH Key Authentication    │
│  - RSA 4096-bit key required        │
│  - No password authentication       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Layer 3: Application User          │
│  - Non-root user (appuser)          │
│  - Limited permissions              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Layer 4: Nginx Proxy               │
│  - Hides backend port               │
│  - Can add SSL termination          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Layer 5: Application Security      │
│  - Environment variables            │
│  - Secret key management            │
└─────────────────────────────────────┘
```
